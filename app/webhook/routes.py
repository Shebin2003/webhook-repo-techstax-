from app.extensions import mongo
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template

webhook = Blueprint('webhook', __name__)

# Helper for 1st, 2nd, 3rd
def ordinal(n):
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    else:
        return f"{n}{['th','st','nd','rd','th','th','th','th','th','th'][n%10]}"
    
@webhook.route('/')
def index():
    return render_template('index.html')

@webhook.route('/github-webhook', methods=['POST'])
def github_webhook():
    payload = request.json
    event = request.headers.get('X-GitHub-Event')

    record = {
        "request_id": "",
        "author": "",
        "action": "",
        "from_branch": "",
        "to_branch": "",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    if event == "push":
        record.update({
            "request_id": payload['head_commit']['id'],
            "author": payload['pusher']['name'],
            "action": "PUSH",
            "from_branch": payload['ref'].split('/')[-1]
        })

    elif event == "pull_request":
        pr = payload['pull_request']
        if payload['action'] == "opened":
            record.update({
                "request_id": str(pr['id']),
                "author": pr['user']['login'],
                "action": "PULL_REQUEST",
                "from_branch": pr['head']['ref'],
                "to_branch": pr['base']['ref']
            })
        elif payload['action'] == "closed" and pr.get("merged", False):
            record.update({
                "request_id": str(pr['id']),
                "author": pr['user']['login'],
                "action": "MERGE",
                "from_branch": pr['head']['ref'],
                "to_branch": pr['base']['ref']
            })

    mongo.db.events.insert_one(record)
    return jsonify({"status": "ok"}), 200

@webhook.route('/events')
def get_events():
    events = list(mongo.db.events.find().sort("timestamp", -1).limit(50))
    for e in events:
        e['_id'] = str(e['_id'])

        # If it's a MERGE action, create the formatted message
        if e['action'] == "MERGE":
            ts_obj = datetime.fromisoformat(e['timestamp'].replace("Z", ""))
            day = ordinal(ts_obj.day)
            formatted_time = ts_obj.strftime(f"{day} %B %Y - %I:%M %p UTC")
            e['message'] = f"\"{e['author']}\" merged branch \"{e['from_branch']}\" to \"{e['to_branch']}\" on {formatted_time}"

    return jsonify(events)

