import re
import datetime
from bson import ObjectId
from flask import Flask, request, redirect, render_template, session
import pymongo
import os.path
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
PROFILE_PATH = APP_ROOT + "/static/profiles"
POST_PATH = APP_ROOT + "/static/posts"
CHAT_PATH = APP_ROOT + "/static/chat"

my_client = pymongo.MongoClient("mongodb+srv://social-dr:W5djwVwCGycp2zDj@cluster0.vw6ep.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
my_database = my_client["chandra"]
admin_col = my_database["admin"]
user_col = my_database["user"]
post_col = my_database["post"]
chat_col = my_database["chat"]
tags_col = my_database["tags"]
report_col = my_database["report"]
friends_col = my_database["friends"]
app = Flask(__name__)
app.secret_key = "user"

video_formats = [".mp4"]
audio_formats = [".mp3"]
image_formats = [".png", ".jpg", ".jpeg"]
pdf_formats = [".pdf"]

query = {"user_name": "admin", "password":"guru"}
count = admin_col.count_documents(query)
if count == 0:
    admin_col.insert_one(query)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin_login_action",methods=['post'])
def admin_login_action():
    user_name = request.form.get("user_name")
    password = request.form.get("password")
    query = {"user_name": user_name, "password": password}
    count = admin_col.count_documents(query)
    if count > 0:
        admin = admin_col.find_one(query)
        session['admin_id'] = str(admin['_id'])
        session['role'] = "admin"
        return redirect("/admin_home")
    else:
        return render_template("message.html",message="Invalid login")


@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")


@app.route("/index_action", methods=['post'])
def index_action():
    user_name = request.form.get("user_name")
    password = request.form.get("password")
    query = {"user_name": user_name, "password": password}
    count = user_col.count_documents(query)
    if count > 0:
        user = user_col.find_one(query)
        if user['status'] == "activated":
            session['user_id'] = str(user['_id'])
            session['user_name'] = user['user_name']
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            session['gender'] = user['gender']
            session['pic'] = user['pic']
            session['email'] = user['email']
            session['password'] = user['password']
            session['pic'] = user['pic']
            session['access_type'] = user['access_type']
            session['dob'] = user['dob']
            session['role'] = "user"
            return redirect("/user_home")
        else:
            return render_template("message.html", message="Your Account Deactivate You can not login")
    else:
        return render_template("message.html",message="invalid Login", get_user_by_user_id=get_user_by_user_id)


@app.route("/user_home")
def user_home():
    post_id = request.args.get("post_id")
    if post_id == None:
        post_id = ""
    user_id = session["user_id"]
    user = user_col.find_one({"_id": ObjectId(user_id)})
    queries = []
    queries.append({"user_id": ObjectId(user_id)})
    queries.append({"access_type": "Public"})
    if 'friends' in user:
        friends = user['friends']
        for friend in friends:
            query = {"user_id": friend, "access_type": "friends"}
            queries.append(query)
    if post_id == "":
        query = {"$or": queries}
    else:
        query = {"_id": ObjectId(post_id)}
    view_type = request.args.get("view_type")
    if view_type!=None:
        if view_type == "shared_by_me":
            query = {"shares.shared_by_user_id": ObjectId(user_id)}
        if view_type == "shared_to_me":
            query = {"shares.shared_to_user_id": ObjectId(user_id)}
    posts = post_col.find(query)
    posts = list(posts)
    posts.reverse()
    return render_template("user_home.html",posts=posts, video_formats=video_formats, audio_formats=audio_formats, image_formats=image_formats, pdf_formats=pdf_formats,is_liked_the_post=is_liked_the_post, post_id=post_id, get_user_by_user_id=get_user_by_user_id,get_comments_by_post_id=get_comments_by_post_id, view_type=view_type, str=str, len=len, get_tags_by_post_id=get_tags_by_post_id)


@app.route("/registration")
def registration():
    return render_template("registration.html")


@app.route("/registration_action", methods=['post'])
def registration_action():
    user_name = request.form.get("user_name")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    gender = request.form.get("gender")
    pic = request.files.get("pic")
    path = PROFILE_PATH + "/" + pic.filename
    pic.save(path)
    email = request.form.get("email")
    password = request.form.get("password")
    access_type = request.form.get("access_type")
    dob = request.form.get("dob")
    status = request.form.get("status")
    query = {"email": email}
    count = user_col.count_documents(query)
    print(email)
    if count == 0:
        query = {"user_name":user_name, "first_name":first_name,"last_name":last_name, "gender": gender,"email":email, "pic": pic.filename,"password":password,"access_type":access_type,"dob":dob,"status":"activated"}
        user_col.insert_one(query)
        return render_template("message.html",message="register successfully")
    else:
        return render_template("message.html",message="Duplicate entry")
    

@app.route("/post")
def post():
    return render_template("post.html")


@app.route("/post_action", methods=['post'])
def post_action(tags=None):
    access_type = request.form.get("access_type")
    caption = request.form.get("caption")
    file = request.files.get("file")
    path = POST_PATH + "/" + file.filename
    file.save(path)
    file_type = os.path.splitext(file.filename)[-1]
    user_id = session["user_id"]
    description = request.form.get("description")
    today = datetime.datetime.today()
    print(today)
    query = {"access_type": access_type, "caption": caption, "file": file.filename, "file_type": file_type, "user_id": ObjectId(user_id), "description": description}
    result = post_col.insert_one(query)
    post_id = result.inserted_id
    tags = request.form.get("tags")
    tags = tags.split(",")
    query = {"user_id": ObjectId(user_id), "post_id": post_id, "tags": tags}
    tags_col.insert_one(query)
    return render_template("message.html",message="post successfully")


def get_tags_by_post_id(post_id):
    query = {"post_id": post_id}
    tag = tags_col.find_one(query)
    if tag!=None:
        return tag['tags']
    else:
        return []


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



@app.route("/users")
def users():
    keyword = request.args.get("keyword")
    user_id = session["user_id"]
    user_type = request.args.get("user_type")
    post_id = request.args.get("post_id")
    if keyword == None:
        keyword = ""
    query = ""
    if user_type == "users":
        if keyword == "":
            query = {"_id": {"$ne": ObjectId(user_id)},  "access_type": "Public" }
        else:
            keyword2 = re.compile(".*"+str(keyword)+".*", re.IGNORECASE)
            query = {"$or": [{"user_name":keyword2, "_id": {"$ne": ObjectId(user_id)},  "access_type": "Public"},{"first_name":keyword2, "_id": {"$ne": ObjectId(user_id)}, "access_type": "Public"},{"last_name":keyword2, "_id": {"$ne": ObjectId(user_id)}, "access_type": "Public"},{"email":keyword2, "_id": {"$ne": ObjectId(user_id)},  "access_type": "Public"}]}
    elif user_type == "following":
        query = {"friend_id": ObjectId(user_id)}
        friends = friends_col.find(query)
        user_ids = []
        for friend in friends:
            user_ids.append(friend['user_id'])
        query = {"_id": {"$in": user_ids}}
    elif user_type == "followers":
        if keyword == "":
            query = {"_id": {"$ne": ObjectId(user_id)}, "friends":ObjectId(user_id)}
        else:
            keyword2 = re.compile(".*"+str(keyword)+".*", re.IGNORECASE)
            query = {"$or": [{"user_name":keyword2, "_id": {"$ne": ObjectId(user_id)},"friends":ObjectId(user_id)},{"first_name":keyword2, "_id": {"$ne": ObjectId(user_id)}, "friends":ObjectId(user_id)},{"last_name":keyword2, "_id": {"$ne": ObjectId(user_id)}, "friends":ObjectId(user_id)},{"email":keyword2, "_id": {"$ne": ObjectId(user_id)}, "friends":ObjectId(user_id)}]}

    users = user_col.find(query)
    users = list(users)

    query = {"_id": ObjectId(user_id)}
    user = user_col.find_one(query)
    friends = []
    if 'friends' in user:
        friends = user["friends"]
    return render_template("users.html", users=users, keyword=keyword, friends=friends, user_type=user_type, post_id=post_id, is_post_shared=is_post_shared, is_friend_following_you=is_friend_following_you, str=str,is_friend_request_sent=is_friend_request_sent, is_friend_blocked_by_you=is_friend_blocked_by_you,ObjectId=ObjectId)


@app.route("/follow")
def follow():
    friend_id = request.args.get("friend_id")
    user_type = request.args.get("user_type")
    user_id = session["user_id"]
    query = {"user_id": ObjectId(user_id), "friend_id": ObjectId(friend_id), "status":"friend requested"}
    friends_col.insert_one(query)
    return redirect("/users?user_type="+str(user_type))

def is_friend_request_sent(friend_id):
    user_id = session["user_id"]
    query = {"user_id": ObjectId(user_id), "friend_id": friend_id, "status": "friend requested"}
    count = friends_col.count_documents(query)
    if count > 0:
        return True
    else:
        return False


@app.route("/unfollow")
def unfollow():
    friend_id = request.args.get("friend_id")
    user_type = request.args.get("user_type")
    user_id = session["user_id"]
    query1 = {"_id": ObjectId(user_id)}
    query2 = {"$pull": {"friends": ObjectId(friend_id)}}
    user_col.update_one(query1, query2)

    query1 = {"_id": ObjectId(friend_id)}
    query2 = {"$pull": {"friends": ObjectId(user_id)}}
    user_col.update_one(query1, query2)

    query = {"user_id": ObjectId(user_id), "friend_id": ObjectId(friend_id)}
    friends_col.delete_one(query)
    return redirect("/users?user_type="+str(user_type))


@app.route("/accept_friend_request")
def accept_friend_request():
    friend_id = request.args.get("friend_id")
    user_type = request.args.get("user_type")
    user_id = session["user_id"]
    query1 = {"_id": ObjectId(user_id)}
    query2 = {"$push": {"friends": ObjectId(friend_id)}}
    user_col.update_one(query1, query2)
    query1 = {"_id": ObjectId(friend_id)}
    query2 = {"$push": {"friends": ObjectId(user_id)}}
    user_col.update_one(query1, query2)
    query = {"friend_id": ObjectId(user_id), "user_id": ObjectId(friend_id)}
    friends_col.delete_one(query)
    return redirect("/users?user_type="+str(user_type))

# @app.route("/unfollow")
# def unfollow():
#     friend_id = request.args.get("friend_id")
#     user_type = request.args.get("user_type")
#     user_id = session["user_id"]
#     query1 = {"_id": ObjectId(user_id)}
#     query2 = {"$pull": {"friends": ObjectId(friend_id)}}
#     user_col.update_one(query1, query2)
#     return redirect("/users?user_type="+str(user_type))


@app.route("/like")
def like():
    post_id = request.args.get("post_id")
    user_id = session['user_id']
    query = {"_id":ObjectId(post_id)}
    query2 = {"$push": {"likes": ObjectId(user_id)}}

    post_col.update_one(query, query2)
    return redirect("user_home#"+str(post_id))


def is_liked_the_post(post_id):
    user_id = session['user_id']
    query = {"_id":post_id, "likes":ObjectId(user_id)}
    count = post_col.count_documents(query)
    if count > 0:
        return True
    else:
        return False


@app.route("/unlike")
def unlike():
    post_id = request.args.get("post_id")
    user_id = session['user_id']
    query = {"_id": ObjectId(post_id)}
    query2 = {"$pull": {"likes": ObjectId(user_id)}}
    post_col.update_one(query, query2)
    return redirect("user_home#"+str(post_id))


@app.route("/comments")
def comments():
    post_id = request.args.get("post_id")
    user_id = session['user_id']
    comment = request.args.get("comment")
    date = datetime.datetime.now()
    query = {"_id": ObjectId(post_id)}
    query2 = {"$push": {"comments": {"user_id": ObjectId(user_id), "comment": comment, "date": date}}}

    post_col.update_one(query, query2)
    return redirect("user_home?post_id="+str(post_id))


def get_comments_by_post_id(post_id):
    query = {"_id": ObjectId(post_id)}
    post = post_col.find_one(query)
    if 'comments' in post:
        comments = post["comments"]
        comments.reverse()
    else:
        comments = []
    return comments


@app.route("/share")
def share():
    post_id = request.args.get("post_id")
    shared_by_user_id = session["user_id"]
    shared_to_user_id = request.args.get("friend_id")
    date = datetime.datetime.now()
    query = {"_id": ObjectId(post_id)}
    query2 = {"$push": {"shares": {"post_id": ObjectId(post_id), "shared_by_user_id": ObjectId(shared_by_user_id),"shared_to_user_id": ObjectId(shared_to_user_id), "date":date }}}
    post_col.update_one(query, query2)
    return redirect("user_home")


def is_post_shared(shared_to_user_id, post_id):
    shared_by_user_id = session['user_id']
    query = {"shares.shared_to_user_id": ObjectId(shared_to_user_id), "shares.shared_by_user_id":ObjectId(shared_by_user_id), "_id":ObjectId(post_id)}
    # query = {"shares":query}
    count = post_col.count_documents(query)
    print(count)
    if count > 0:
        return True
    else:
        return False


def is_friend_following_you(friend_id):
    user_id = session['user_id']
    user_id = ObjectId(user_id)
    query = {"_id": friend_id, "friends":user_id}
    count = user_col.count_documents(query)
    if count > 0:
        return True
    else:
        return False


@app.route("/get_messages")
def get_messages():
    other_user_id = request.args.get('other_user_id')
    user_id = session['user_id']
    query = {"$or": [{"sender_id": ObjectId(user_id), "receiver_id": ObjectId(other_user_id)}, {"sender_id": ObjectId(other_user_id), "receiver_id": ObjectId(user_id)}]}
    messages = chat_col.find(query)
    messages2 = []
    for message in messages:
        message['_id'] = str(message['_id'])
        message['sender_id'] = str(message['sender_id'])
        message['receiver_id'] = str(message['receiver_id'])
        messages2.append(message)

    return {"messages": messages2}


@app.route("/get_message")
def get_message():
    other_user_id = request.args.get('other_user_id')
    user_id = session['user_id']
    query = {"$or": [{"sender_id": ObjectId(user_id), "receiver_id": ObjectId(other_user_id), "isSenderRead": 'unread'},
                     {"sender_id": ObjectId(other_user_id), "receiver_id": ObjectId(user_id), "isReceiverRead": 'unread'}]}
    messages = chat_col.find(query)
    messages = list(messages)
    for message in messages:
        if str(message['sender_id']) == user_id:
            query = {"_id": message['_id']}
            query2 = {"$set": {"isSenderRead": 'read'}}
            chat_col.update_one(query, query2)
        elif str(message['receiver_id']) == user_id:
            query = {"_id": message['_id']}
            query2 = {"$set": {"isReceiverRead": 'read'}}
            chat_col.update_one(query, query2)
    messages2 = []
    for message in messages:
        message['_id'] = str(message['_id'])
        message['sender_id'] = str(message['sender_id'])
        message['receiver_id'] = str(message['receiver_id'])
        messages2.append(message)
    return {"messages": messages2}


@app.route("/send_messages")
def send_messages():
    other_user_id = request.args.get('other_user_id')
    user_id = session['user_id']
    message = request.args.get('message')
    query = {"sender_id": ObjectId(user_id), "receiver_id": ObjectId(other_user_id), "message": message,"isSenderRead":'unread', "isReceiverRead":'unread', "date": datetime.datetime.now().strftime("%d-%m-%Y %I:%M %p")}
    chat_col.insert_one(query)
    return {"status": "ok"}

@app.route("/send_message_file", methods=['post'])
def send_message_file():
    other_user_id = request.form.get('other_user_id')
    message = request.form.get('message')
    file = request.files.get("file")
    path = CHAT_PATH + "/"+file.filename
    file.save(path)
    user_id = session['user_id']
    file_type = os.path.splitext(file.filename)[-1]
    query = {"sender_id": ObjectId(user_id), "receiver_id": ObjectId(other_user_id), "message": message,"isSenderRead":'unread', "isReceiverRead":'unread', "date": datetime.datetime.now().strftime("%d-%m-%Y %I:%M %p"),"file":file.filename, "file_type":file_type}
    chat_col.insert_one(query)
    return {"status": "ok"}

@app.route("/set_as_read_receiver")
def set_as_read_receiver():
    other_user_id = request.args.get('other_user_id')
    user_id = session['user_id']
    query = {"sender_id": ObjectId(other_user_id), "receiver_id": ObjectId(user_id)}
    query2 = {"$set":{"isReceiverRead": "read"}}
    chat_col.update_one(query,query2)
    return {"status": "ok"}


@app.route("/set_as_read_sender")
def set_as_read_sender():
    other_user_id = request.args.get('other_user_id')
    user_id = session['user_id']
    query = {"sender_id": ObjectId(user_id), "receiver_id": ObjectId(other_user_id)}
    query2 = {"$set": {"isSenderRead": "read"} }
    chat_col.update_one(query, query2)
    return {"status": "ok"}


@app.route("/chat")
def chat():
    user_id = session["user_id"]
    user = user_col.find_one({"_id": ObjectId(user_id)})
    seller_name = user['user_name']
    other_user_id = request.args.get('other_user_id')
    user_id = ObjectId(session['user_id'])
    query = {"sender_id": user_id}
    query2 = {"receiver_id": user_id}
    friends = set({})
    results = chat_col.find({"$or": [query, query2]})
    for result in results:
        if user_id != result['receiver_id']:
            friends.add(result['receiver_id'])
        if user_id != result['sender_id']:
            friends.add(result['sender_id'])
    query4 = {"_id": {"$in": list(friends)}}
    users = user_col.find(query4)
    return render_template("chat.html", users=users, seller_id=user_id, seller_name=seller_name, str=str)


@app.route("/block")
def block():
    friend_id = request.args.get("friend_id")
    print(friend_id)
    user_id = session['user_id']
    query = {"_id":ObjectId(user_id)}
    query2 = {"$push":{"blocked_ids": ObjectId(friend_id)}}
    user_col.update_one(query, query2)
    return render_template("message.html",message="User Blocked",friend_id=friend_id)


@app.route("/unblock")
def unblock():
    friend_id = request.args.get("friend_id")
    print(friend_id)
    user_id = session['user_id']
    query = {"_id":ObjectId(user_id)}
    query2 = {"$pull":{"blocked_ids": ObjectId(friend_id)}}
    user_col.update_one(query, query2)
    return render_template("message.html",message="User Unblocked",friend_id=friend_id)


def is_friend_blocked_by_you(friend_id):
    user_id = session['user_id']
    query = {"_id": ObjectId(user_id), "blocked_ids": friend_id}
    count = user_col.count_documents(query)
    if count > 0:
        return True
    else:
        return False

@app.route("/report")
def report():
    friend_id = request.args.get("friend_id")

    return render_template("report.html",friend_id=friend_id)


@app.route("/report_description",methods=['post'])
def report_description():
    friend_id = request.form.get("friend_id")
    report = request.form.get("report")
    user_id = session['user_id']

    query = {"friend_id":ObjectId(friend_id),"report":report, "user_id":ObjectId(user_id), "date": datetime.datetime.now()}
    report_col.insert_one(query)
    return render_template("message.html",message="reported successfully")

@app.route("/view_reports")
def view_reports():
    reports = report_col.find()
    reports = list(reports)
    reports.reverse()
    return render_template("view_reports.html",reports=reports, get_user_by_user_id=get_user_by_user_id,get_friend_by_friend_id=get_friend_by_friend_id)

def get_user_by_user_id(user_id):
    query = {"_id": user_id}
    user = user_col.find_one(query)
    return user

def get_friend_by_friend_id(friend_id):
    query = {"_id": friend_id}
    friend = friends_col.find_one(query)
    return friend

@app.route("/deactivated")
def deactivated():
    user_id = request.args.get("user_id")
    query = {"_id": ObjectId(user_id)}
    query2 = {"$set": {"status": "Deactivated"}}
    user_col.update_one(query, query2)
    return redirect("/view_reports")
if __name__ == "__main__":
    app.run(debug=True)




