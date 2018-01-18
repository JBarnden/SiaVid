from flask import Flask, request
import json

app = Flask(__name__)

@app.route("/getMiners/")
def listMiners():
	minerList = {'firstminerinternalname': 'First Miner', 'secondminerinternalname': 'Second Miner', 'thirdminerinternalname': 'Third Miner'}
	return json.dumps(minerList)

@app.route("/ready/<miner>")
def checkReady(miner):
	return json.dumps(False)

@app.route("/search/<miner>", methods=['POST'])
def doSearch(miner):
	terms = request.form['searchterms']
	

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    if name is None:
	return "No name"
    return name

if __name__ == "__main__":
    app.run()
