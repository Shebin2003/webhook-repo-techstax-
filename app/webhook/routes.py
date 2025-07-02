from app.extensions import mongo
from datetime import datetime, timezone
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
    now = datetime.now(timezone.utc)
    day = ordinal(now.day)
    formatted_time = now.strftime(f"{day} %B %Y - %I:%M %p UTC")
    payload = request.json
    event = (request.headers.get('X-GitHub-Event') or "").lower()

    record = {
        "request_id": "",
        "author": "",
        "action": "",
        "from_branch": "",
        "to_branch": "",
        "timestamp": formatted_time
    }
    print("event: ",event)
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
    else:
        print("hello",record)
    mongo.db.events.insert_one(record)
    return jsonify({"status": "ok"}), 200

@webhook.route('/events')
def get_events():
    events = list(mongo.db.events.find().sort("timestamp", -1).limit(50))
    for e in events:
        e['_id'] = str(e['_id'])
        
        ts = e.get('timestamp', '')
        action = e.get('action', '').upper()  # <-- FIX HERE
        if e['action'] == "MERGE":
            e['message'] = f"\"{e.get('author','')}\" merged branch \"{e.get('from_branch','')}\" to \"{e.get('to_branch','')}\" on {ts}"
        elif e['action'] == "PUSH":
            e['message'] = f"\"{e.get('author','')}\" pushed to \"{e.get('from_branch','')}\" on {ts}"
        elif e['action'] == "PULL_REQUEST":
            e['message'] = f"\"{e.get('author','')}\" submitted a pull request from \"{e.get('from_branch','')}\" to \"{e.get('to_branch','')}\" on {ts}"
        else:
            e['message'] = f"\"{e.get('author','')}\" did \"{action}\" on branch \"{e.get('from_branch','')}\" at {ts}"

    return jsonify(events)



