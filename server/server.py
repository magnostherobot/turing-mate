from flask import Flask
from flask import request
import json
app = Flask(__name__)


currently_active = {}

@app.route('/',methods=["GET,POST"], defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    data = request.data.decode()
    data = json.loads(data)
    print("Received " + data)
    # print(request.data.decode())
    type = data['type']

    if type == "register":
        if type not in currently_active:
            currently_active[path] = {}
            currently_active[path]['P1'] = {}
            currently_active[path]['P1']['addr'] = request.remote_addr
        else:
            currently_active[path]['P2'] = {}
            currently_active[path]['P2']['addr'] = request.remote_addr
    if type == "quit":
        if type in currently_active:
            del currently_active[type]


    return "yeetsify " + str(path), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0")
