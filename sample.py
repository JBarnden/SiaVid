import json

from flask import Flask, request

from pipeline import Pipeline, DataMinerAdapter
from exampleplugins import SplitDataMiner

app = Flask(__name__)

pl = Pipeline()

@app.route("/getMiners/")
def listMiners():
	return json.dumps(pl.listMiners())

@app.route("/ready/<miner>", methods=['GET'])
def checkReady(miner):
    if miner in pl.listMiners():
        pass
        #return status of miner
        #return json.dumps(pl.mine[miner].getStatus()
    else:
        #return some error we haven't worked out yet
        return json.dumps(False)

@app.route("/search/<miner>", methods=['POST'])
def doSearch(search):
    if search in pl.listSearch():
        terms = request.form['searchterms']
        results = pl.search[search].doSearch(terms)
        return json.dumps(results)
    else:
        #return some error we haven't worked out ye
        return json.dumps(False)

if __name__ == "__main__":
    pl.addMiner(DataMinerAdapter(SplitDataMiner()), 'split')
    app.run()