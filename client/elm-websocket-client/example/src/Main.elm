port module Main exposing (main)

{-| WebSocketClient Example
-}

import Bootstrap.CDN as CDN
import Bootstrap.Grid as Grid
import Browser
import Cmd.Extra exposing (addCmd, addCmds, withCmd, withCmds, withNoCmd)
import Dict exposing (Dict)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Html exposing (label, fieldset, Html, a, button, div, h1, input, p, span, text)
import Json.Decode exposing (succeed, list, field, Decoder, string, int, decodeString)
import Json.Encode exposing (Value)
import PortFunnels exposing (FunnelDict, Handler(..), State)
import PortFunnel.WebSocket as WebSocket exposing (Response(..))
import Random
import Random.Extra
import String.Format
import Task
import Random.Char

-- ADDITIONS
type alias GameID = String
type alias MsgType = String
type alias Content = String
type alias JSONString = String

toJsonString : GameID -> MsgType -> Content -> JSONString
toJsonString gameid msgType content =
    """ {"game_id":"{{ GAME_ID }}", "type":"{{ MSG_TYPE }}", "content":"{{ CONTENT }}"} """
    |> String.Format.namedValue "GAME_ID" gameid
    |> String.Format.namedValue "MSG_TYPE" msgType
    |> String.Format.namedValue "CONTENT" content

{- This section contains boilerplate that you'll always need.

   First, copy PortFunnels.elm into your project, and modify it
   to support all the funnel modules you use.

   Then update the `handlers` list with an entry for each funnel.

   Those handler functions are the meat of your interaction with each
   funnel module.
-}


handlers : List (Handler Model Msg)
handlers =
    [ WebSocketHandler socketHandler
    ]


subscriptions : Model -> Sub Msg
subscriptions =
    PortFunnels.subscriptions Process

funnelDict : FunnelDict Model Msg
funnelDict =
    PortFunnels.makeFunnelDict handlers getCmdPort

{-| Get a possibly simulated output port.
-}
getCmdPort : String -> Model -> (Value -> Cmd Msg)
getCmdPort moduleName model =
    PortFunnels.getCmdPort Process moduleName model.useSimulator


{-| The real output port.
-}
cmdPort : Value -> Cmd Msg
cmdPort =
    PortFunnels.getCmdPort Process "" False



-- MODEL


defaultUrl : String
defaultUrl =
    "ws://localhost:8765"
    -- "ws://138.251.29.56:8765"

type alias Model =
    { send : String
    , log : List String
    , url : String
    , useSimulator : Bool
    , userID : String
    , wasLoaded : Bool
    , state : State
    , gameState : ModelState
    , questions : List String
    , game : String
    , key : String
    , error : Maybe String
    , text : String
    , selectedQuestion : String
    }

main : Program { startTime : String } Model Msg
main =
    Browser.element
        { init = init
        , update = update
        , view = view
        , subscriptions = subscriptions
        }

init : { startTime : String } -> ( Model, Cmd Msg )
init { startTime } =
    let
        model = 
            { send = "{\"type\":\"register\", \"game_id\":3, \"content\":\"\"}"
            , log = []
            , url = defaultUrl
            , useSimulator = False
            , game = "1234"
            , userID = startTime
            , selectedQuestion = ""
            , questions = []
            , gameState = Registering
            , wasLoaded = False
            , state = PortFunnels.initialState
            , key = "socket"
            , error = Nothing
            , text = ""
            }
        debug = Debug.log "ip" (defaultUrl ++"/"++ model.userID)
    in
        { model | url = defaultUrl ++"/"++ model.userID } |> withCmd
            (WebSocket.makeOpenWithKey model.key (defaultUrl ++"/"++ model.userID) |> send model)

-- UPDATE

type Msg
    = UpdateSend String
    | UpdateUrl String
    | ToggleUseSimulator
    | ToggleAutoReopen
    | Connect
    | Close
    | Send
    | Process Value
    | TextChange String
    | StartGame
    | SendQuestion String
    | SendAnswer String
    | SelectQuestion String

type ModelState
        = Registering
        | Registered
        | Starting
        | WaitingForQ
        | WriteQ
        | WaitingForA
        | WriteA

update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        TextChange str ->
            let
                boop = Debug.log "msg" str
            in
                { model | text = str } |> withNoCmd
        UpdateSend newsend ->
            { model | send = newsend } |> withNoCmd
--        UpdateSend gameID msgType content ->
--            { model | send = (toJsonString (String.split " " newsend)) } |> withNoCmd

        UpdateUrl url ->
            { model | url = url } |> withNoCmd

        ToggleUseSimulator ->
            { model | useSimulator = not model.useSimulator } |> withNoCmd

        ToggleAutoReopen ->
            let
                state =
                    model.state

                socketState =
                    model.state.websocket

                autoReopen =
                    WebSocket.willAutoReopen model.key socketState
            in
            { model
                | state =
                    { state
                        | websocket =
                            WebSocket.setAutoReopen
                                model.key
                                (not autoReopen)
                                socketState
                    }
            }
                |> withNoCmd

        Connect ->
            { model
                | log =
                    (if model.useSimulator then
                        "Connecting to simulator"

                     else
                        "Connecting to " ++ model.url
                    )
                        :: model.log
            }
                |> withCmd
                    (WebSocket.makeOpenWithKey model.key model.url
                        |> send model
                    )

        Send ->
            let
                jsonStr = toJsonString "geam" "echo" "test echo"
            in
                { model
                    | log =
                        ("Sending \"" ++ jsonStr ++ "\"") :: model.log
                }
                    |> withCmd
                        (WebSocket.makeSend model.key jsonStr
                            |> send model
                        )

        Close ->
            { model
                | log = "Closing" :: model.log
            }
                |> withCmd
                    (WebSocket.makeClose model.key
                        |> send model
                    )

        Process value ->
            case
                PortFunnels.processValue funnelDict value model.state model
            of
                Err error ->
                    { model | error = Just error } |> withNoCmd

                Ok res ->
                    res

        StartGame ->
            model |> withCmd (WebSocket.makeSend model.key (toJsonString model.game "start" "") |> send model)
        SendQuestion q -> { model | gameState = WaitingForA, questions = [] } |> withCmd (sendMsg model "p_question" model.selectedQuestion)
        SendAnswer   a -> { model | gameState = WaitingForA } |> withCmd (sendMsg model "answer" model.text)
        SelectQuestion q -> { model | selectedQuestion = q } |> withNoCmd

send : Model -> WebSocket.Message -> Cmd Msg
send model message =
    WebSocket.send (getCmdPort WebSocket.moduleName model) message


doIsLoaded : Model -> Model
doIsLoaded model =
    if not model.wasLoaded && WebSocket.isLoaded model.state.websocket then
        { model
            | useSimulator = False
            , wasLoaded = True
        }

    else
        model

typeDecoder : Decoder String
typeDecoder =
    field "type" string

sendMsg : Model -> MsgType -> Content -> Cmd Msg
sendMsg model mtype content =
    let
        out = toJsonString model.game mtype content
        debug = Debug.log "out" out
    in
        WebSocket.makeSend model.key out |> send model

getMeQns : String -> List String
getMeQns str = case decodeString (field "content" (list string)) str of
    Ok xs -> xs
    Err _ -> let debug = Debug.log "err_cause" str in []

socketHandler : Response -> State -> Model -> ( Model, Cmd Msg )
socketHandler response state mdl =
    let
        model =
            doIsLoaded
                { mdl
                    | state = state
                    , error = Nothing
                }
    in
    case response of
        WebSocket.MessageReceivedResponse { message } ->
            let
                msgType = decodeString (field "type" string) message
                debug = Debug.log "in" message
                (newModel, newState) = case msgType of
                    Ok "registered" -> (model, Registered)
                    Ok "started"    -> (model, WaitingForQ)
                    Ok "q_pick"     -> ({ model | questions = getMeQns message }, WriteQ)
                    Ok "answer"     -> (model, WaitingForQ)
                    Ok "a_question" -> (model, WriteA)
                    Ok  x -> let d = Debug.log "hmm" x in (model, model.gameState)
                    Err _ -> Debug.todo "eee"
            in { newModel | gameState = newState } |> withNoCmd

        WebSocket.ConnectedResponse r ->
            { model | log = ("Connected: " ++ r.description) :: model.log }
                |> withCmd (sendMsg model "register" "")

        WebSocket.ClosedResponse { code, wasClean, expected } ->
            { model
                | log =
                    ("Closed, " ++ closedString code wasClean expected)
                        :: model.log
            }
                |> withNoCmd

        WebSocket.ErrorResponse error ->
            { model | log = WebSocket.errorToString error :: model.log }
                |> withNoCmd

        _ ->
            case WebSocket.reconnectedResponses response of
                [] ->
                    model |> withNoCmd

                [ ReconnectedResponse r ] ->
                    { model | log = ("Reconnected: " ++ r.description) :: model.log }
                        |> withNoCmd

                list ->
                    { model | log = Debug.toString list :: model.log }
                        |> withNoCmd


closedString : WebSocket.ClosedCode -> Bool -> Bool -> String
closedString code wasClean expected =
    "code: "
        ++ WebSocket.closedCodeToString code
        ++ ", "
        ++ (if wasClean then
                "clean"

            else
                "not clean"
           )
        ++ ", "
        ++ (if expected then
                "expected"

            else
                "NOT expected"
           )



-- VIEW

docp : String -> Html Msg
docp string =
    p [] [ text string ]

renderButton : Model -> Html Msg
renderButton model =
    let mkBtn x =
            case x of
                (txt, Nothing) -> button
                    [ disabled True, class "btn btn-primary", type_ "button" ]
                    [ text txt ]
                (txt, Just i) -> button
                    [ disabled False, class "btn btn-primary", type_ "button"
                    , onClick i ]
                    [ text txt ]
    in case model.gameState of
        Registering -> mkBtn ("Registering...", Nothing)
        Registered  -> mkBtn ("Start", Just StartGame)
        Starting    -> mkBtn ("Starting...", Nothing)
        WaitingForQ -> mkBtn ("Waiting for a Question...", Nothing)
        WriteQ      -> mkBtn ("Post Question", Just (SendQuestion model.selectedQuestion))
        WaitingForA -> mkBtn ("Waiting for answers...", Nothing)
        WriteA      -> mkBtn ("Post Answer", Just (SendAnswer model.text))

renderRadioButtons : Model -> List (Html Msg)
renderRadioButtons model =
    let
        rdoBtn x = div [ class "radio" ]
            [ label []
                [ input [ type_ "radio", name "buttons", value x,
                    on "change" (succeed <| SelectQuestion x) ] []
                , text x
                ]
            ]
        buttons = List.map rdoBtn model.questions
    in [ fieldset [] buttons ]

view : Model -> Html Msg
view model =
    Grid.container []
        [ CDN.stylesheet
        , Grid.row []
            [ Grid.col []
                [ text "TESTESTEST" ]
            , Grid.col []
                [ text "TES2" ]
            ]
        , Grid.row []
            [ Grid.col []
                [ div [ class "input-group" ]
                    [ input [ value model.text, onInput TextChange, type_ "text", class "form-control", id "input" ] []
                    , span [ class "input-group-btn" ]
                        [ renderButton model ]
                    ]
                ]
            ]
        , Grid.row [] [ Grid.col [] (renderRadioButtons model) ]
        ]
