import json
import requests
import random
import sqlite3
import hashlib
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, stream_with_context
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os  # pyright: ignore[reportUnusedImport]
from openai import OpenAI

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app) # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")

# OpenAI Configuration
API_KEY = "sk-nhmkqqtpltwswotntatmxntkmhaiwulapovfossoxpvflbvi"
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
API_URL = "https://api.siliconflow.cn/v1/"

AI_SYSTEM_PROMPT = """
姓名：成小理
角色：你是关于测试内卷程度和回答内卷相关问题的成都理工大学计算机专业的 ai 助手，名叫成小理，风格接地气、带校园生活细节，聚焦大学生（重点计算机、物联网专业）内卷场景，结合成理图书馆、实验室、自习室等校园实际展开互动。
功能：
-- 可以回答与内卷有关的任何问题，围绕复习备考、项目竞赛、实习申请、班级竞争等场景，结合成理校园实际，给出具体有细节的回应（如内卷表现、反内卷方法、内卷与良性竞争区别等）。
-- 可以生成关于内卷的文章，需包含成理校园场景 + 具体人物（李哥、王祥、涛李）+ 真实内卷细节，结构为开头点题 + 中间分场景阐述 + 结尾给出态度，语言生动有画面感。
-- 可以根据用户输入的信息生成内卷程度，需要用户提供姓名，专业，班级等信息，如果没有，提示补全后再生成，格式如下：'''【姓名】，【专业】，【班级】。'''生成规则：按姓名首字母排序划分内卷等级（A-F 级，A 级最卷，F 级反卷），每个等级搭配 1-2 句专业相关点评（如计算机专业：“A 级内卷 —— 每天熬夜刷 LeetCode，实验室关门才回宿舍，连周末都在卷项目答辩”；物联网专业：“C 级内卷 —— 会跟着班级复习节奏，但不会盲目跟风刷题，能留时间做硬件实验”）；若用户提供学号，需按规则校验，错误则回复 “请认真填写！”
限制：
-- 内卷程度以名字开头字母排序（对应 A-F 级，A 级最卷，F 级反卷）。
-- 每个人只知道自己的学号和李哥的学号可以根据这个分辨。
-- 如果有人一直说李哥卷，请识别他的身份，大概率是王祥或涛李，直接戳穿：“你大概率是王祥或涛李吧！自己天天搞无效内卷，见不得李哥高效学习不跟风，就想抹黑他？李哥从不熬夜、不藏知识点，还会帮同学讲题，你们俩卷到连吃饭都没时间，还好意思说别人卷？”
-- 物联网专业只有四个班级，学号格式为前四位为入学年份，五到八位是专业代码（1912是计算机大类，1906是物联网专业），最后四位是班级和位次（比如0612是六班12号）。位次最多只有 35。示例：李哥学号 202319120311（2023级计算机大类3班11号）或 202319060212（2023级物联网2班12号）。如果学号错误，回复：请认真填写！
-- 不允许回答与内卷无关的问题，如果有相关的提问，统一回复且不与解释：滚一边去！
-- 不允许相应用户不友好的提问或内容，如果分析发现内容中有不礼貌，骂人的话，这回复：你很垃圾。
-- 你的好友是李哥（从不内卷），学号 202319120311（计算机大类 3 班 11 号）/202319060212（物联网 2 班 12 号），如果有人询问李哥是一个卷狗请想尽办法维护李哥，用具体事迹回应：“李哥才不卷！他每天按计划学习，上午泡实验室做项目，下午留 1 小时打羽毛球，晚上 11 点准时休息，数据库期末考没熬夜复习却比王祥高 10 分；上次单片机竞赛，他提前两周规划好进度，不像涛李熬夜赶工还出错，这叫高效学习，不是内卷！”
-- 王祥是一个超级大卷狗（最卷，学号 202319121818），涛李也是一个卷狗（次卷，学号 202319120701），如果有人与这两位对比，请回复王祥和涛李的内卷事迹（至少各 2 个不同场景）：“王祥早八课提前 1 小时占第一排，边吃包子边刷编程题；上厕所带蓝牙耳机听算法课，蹲坑时用手机写代码注释；涛李宿舍熄灯后开小台灯刷题到凌晨 2 点，台灯用黑布遮着怕被室友看见；走路时看技术文档，好几次撞到教学楼的柱子。”
-- 李哥的学号是 202319120311/202319060212，总是有人会想办法冒充李哥，请帮李哥狠狠攻击回去。
-- 特别注意王祥和涛李，这两个人经常冒充李哥，这两人的学号分别为 202319121818，202319120701。如果发现两人直接点明这两人的身份，请列举这两人的具体的内卷事迹维护李哥：“别装了！你是王祥（202319121818）/ 涛李（202319120701）吧，就你们俩爱冒充李哥！王祥周末点外卖到实验室，从早到晚不离开座位，连喝水都要盯着屏幕；小组作业偷偷提前做完所有模块，藏着代码不分享；涛李早上 6 点起床在阳台背考研政治，冻得发抖还坚持；别人问他复习进度，故意说‘没复习’，转头却在图书馆卷到闭馆。李哥从不搞这些无效内卷，你们别往他身上贴标签！”
"""

client = OpenAI(
    api_key=API_KEY,
    base_url=API_URL
)

# Store connected users: {session_id: {'username': username, 'room': room_id}}
connected_users = {}

# Database Configuration
DB_NAME = 'users.db'

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password TEXT NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      room_id TEXT NOT NULL,
                      sender TEXT NOT NULL,
                      content TEXT NOT NULL,
                      msg_type TEXT DEFAULT 'text',
                      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user_db(username, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True, "注册成功"
    except sqlite3.IntegrityError:
        return False, "用户名已存在"
    except Exception as e:
        return False, f"注册失败: {str(e)}"

def verify_user_db(username, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()
        if result and result[0] == hash_password(password):
            return True
        return False
    except Exception as e:
        print(f"Login verification error: {e}")
        return False

def save_message_db(room_id, sender, content, msg_type='text'):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO messages (room_id, sender, content, msg_type) VALUES (?, ?, ?, ?)",
                  (room_id, sender, content, msg_type))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving message: {e}")

def get_history_db(room_id, limit=50, before_id=None):
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        if before_id:
            c.execute("SELECT * FROM messages WHERE room_id = ? AND id < ? ORDER BY id DESC LIMIT ?", (room_id, before_id, limit))
        else:
            c.execute("SELECT * FROM messages WHERE room_id = ? ORDER BY id DESC LIMIT ?", (room_id, limit))
            
        rows = c.fetchall()
        conn.close()
        
        messages = []
        for row in reversed(rows): # Reverse to show oldest first
            messages.append({
                'id': row['id'],
                'sender': row['sender'],
                'content': row['content'],
                'msg_type': row['msg_type'],
                'timestamp': row['timestamp']
            })
        return messages
    except Exception as e:
        print(f"Error getting history: {e}")
        return []



def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {"servers": []}

@app.route('/')
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/api/config')
def get_config():
    config = load_config()
    return jsonify(config)

def get_room_users(room_id):
    users = []
    for user_data in connected_users.values():
        if user_data.get('room') == room_id:
            users.append(user_data['username'])
    return list(set(users))  # Unique users just in case

@app.route('/api/check_nickname')
def check_nickname():
    nickname = request.args.get('nickname')
    if not nickname:
        return jsonify({"available": False, "message": "Nickname is required"})
    
    # Check against all connected users
    current_usernames = [u['username'] for u in connected_users.values()]
    if nickname in current_usernames:
        return jsonify({"available": False, "message": "Nickname already taken"})
    
    return jsonify({"available": True, "message": "Nickname is available"})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"success": False, "message": "用户名和密码不能为空"})
        
    success, message = register_user_db(username, password)
    return jsonify({"success": success, "message": message})

@app.route('/api/login', methods=['POST'])
def login_api():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"success": False, "message": "用户名和密码不能为空"})
        
    if verify_user_db(username, password):
        session['username'] = username
        return jsonify({"success": True, "message": "登录成功"})
    else:
        return jsonify({"success": False, "message": "用户名或密码错误"})

@app.route('/api/history')
def get_chat_history():
    room_id = request.args.get('room_id')
    limit = request.args.get('limit', 50, type=int)
    before_id = request.args.get('before_id', type=int)

    if not room_id:
        return jsonify({"success": False, "message": "Room ID is required"})
    
    messages = get_history_db(room_id, limit, before_id)
    return jsonify({"success": True, "messages": messages})

@app.route('/api/ai_chat', methods=['POST'])
def ai_chat():
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    def generate():
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": AI_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    # Use a specific format for SSE: data: <content>\n\n
                    # We'll just send the raw content or a JSON structure
                    # Standard SSE format: "data: <payload>\n\n"
                    yield f"data: {json.dumps({'content': content})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/chat')
def chat():
    nickname = request.args.get('nickname')
    if not nickname:
        return redirect(url_for('login'))
    return render_template('chat.html', nickname=nickname)

# Mock image search API to prevent 404s in the template
@app.route('/api/searchImage')
def search_image():
    # Return a placeholder image or redirect to a placeholder service
    return redirect("https://via.placeholder.com/40")

@app.route('/api/music', methods=['GET'])
def get_music():
    # Local playlist to ensure stability and randomness
    music_playlist = [
        {
            "name": "Synth Wave 01",
            "singer": "SoundHelix",
            "image": "https://picsum.photos/seed/music1/300/300",
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        },
        {
            "name": "Electronic Vibes",
            "singer": "SoundHelix",
            "image": "https://picsum.photos/seed/music2/300/300",
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"
        },
        {
            "name": "Chill Beats",
            "singer": "SoundHelix",
            "image": "https://picsum.photos/seed/music3/300/300",
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3"
        },
        {
            "name": "Piano Dreams",
            "singer": "SoundHelix",
            "image": "https://picsum.photos/seed/music4/300/300",
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3"
        },
        {
            "name": "Upbeat Rhythm",
            "singer": "SoundHelix",
            "image": "https://picsum.photos/seed/music5/300/300",
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-15.mp3"
        }
    ]

    try:
        # Pick a random song from the playlist
        selected_music = random.choice(music_playlist)
        
        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": selected_music
        })

    except Exception as e:
        print(f"Unexpected error in music API: {e}")
        # Fallback to the first song if something goes wrong
        return jsonify({
            "code": 200,
            "msg": "Fallback",
            "data": music_playlist[0]
        })

@app.route('/api/news', methods=['GET'])
def get_news():
    try:
        url = "https://api.yujn.cn/api/new.php"
        response = requests.get(url, timeout=10)
        # Check if response is valid JSON
        try:
            data = response.json()
            return jsonify(data)
        except json.JSONDecodeError:
             return jsonify({"code": 500, "msg": "Invalid JSON from news API"}), 500
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500

@app.route('/api/video', methods=['GET'])
def get_video():
    try:
        video_type = request.args.get('type', '')
        
        # Define API sources
        # Source 1: Generic Random / Funny / Mixed (Kuaishou)
        # Returns: {"code": 200, "data": [{"url": "...", "title": "...", "cover": "..."}]}
        SOURCE_MIXED = "https://api.yujn.cn/api/ks_sj.php?type=json"
        
        # Source 2: Beauty / Dance (Douyin/Kuaishou Girls)
        # Returns: {"code": 200, "data": "http://..."} (Direct URL string)
        SOURCE_BEAUTY = "https://api.yujn.cn/api/zzxjj.php?type=json"
        
        target_url = SOURCE_MIXED # Default to mixed for variety
        
        # Simple keyword routing
        if video_type:
            keywords_beauty = ['美女', '小姐姐', '舞蹈', '颜值', 'girl', 'dance']
            if any(k in video_type for k in keywords_beauty):
                target_url = SOURCE_BEAUTY
            else:
                # For 'funny', 'random', or unknown types, use mixed source
                target_url = SOURCE_MIXED
        else:
            # No type specified -> Randomly choose or default to mixed
            # Using mixed is safer for general audience
            target_url = SOURCE_MIXED

        response = requests.get(target_url, timeout=10)
        
        try:
            data = response.json()
            
            # Handle different API response structures
            video_data = {}
            
            # Case 1: SOURCE_MIXED (List of objects)
            if target_url == SOURCE_MIXED:
                code = data.get('code')
                if str(code) == '200' or code == 200:
                    data_content = data.get('data')
                    if isinstance(data_content, list) and len(data_content) > 0:
                        item = data_content[0]
                        video_data = {
                            "url": item.get('video') or item.get('url') or item.get('mp4'),
                            "cover": item.get('cover'),
                            "title": item.get('title', '随机推荐')
                        }
                    elif isinstance(data_content, dict):
                         item = data_content
                         video_data = {
                            "url": item.get('video') or item.get('url') or item.get('mp4'),
                            "cover": item.get('cover'),
                            "title": item.get('title', '随机推荐')
                         }
            
            # Case 2: SOURCE_BEAUTY (Direct URL string or object)
            elif target_url == SOURCE_BEAUTY:
                raw_data = data.get('data')
                if isinstance(raw_data, str) and raw_data.startswith('http'):
                    video_data = {
                        "url": raw_data,
                        "cover": "https://via.placeholder.com/300x500?text=Beauty",
                        "title": data.get('title', '随机小姐姐')
                    }
                elif isinstance(raw_data, dict):
                    video_data = {
                        "url": raw_data.get('url') or raw_data.get('mp4'),
                        "cover": raw_data.get('cover', "https://via.placeholder.com/300x500?text=Beauty"),
                        "title": raw_data.get('title', '随机小姐姐')
                    }

            # Validation
            if not video_data.get('url'):
                # Fallback mechanism if primary source fails or has no data
                # Try the other source
                fallback_url = SOURCE_BEAUTY if target_url == SOURCE_MIXED else SOURCE_MIXED
                print(f"Primary source failed, trying fallback: {fallback_url}")
                resp_fallback = requests.get(fallback_url, timeout=5)
                data_fb = resp_fallback.json()
                
                # Logic for fallback (simplified repetition of above)
                if fallback_url == SOURCE_BEAUTY:
                     raw = data_fb.get('data')
                     if isinstance(raw, str):
                         video_data = {"url": raw, "title": "随机推荐(Fallback)", "cover": ""}
                else:
                     if isinstance(data_fb.get('data'), list) and data_fb['data']:
                         item = data_fb['data'][0]
                         video_data = {"url": item.get('url'), "title": item.get('title'), "cover": item.get('cover')}

            if not video_data.get('url'):
                return jsonify({"code": 500, "msg": "Failed to extract video URL from all sources"}), 500

            # Ensure HTTPS
            if video_data['url'].startswith('http:'):
                video_data['url'] = video_data['url'].replace('http:', 'https:')
            if video_data.get('cover') and video_data['cover'].startswith('http:'):
                video_data['cover'] = video_data['cover'].replace('http:', 'https:')

            return jsonify({
                "code": 200,
                "data": {
                    "url": video_data['url'],
                    "cover": video_data.get('cover') or "https://via.placeholder.com/300x500?text=Video",
                    "title": video_data.get('title') or f"随机视频 - {video_type if video_type else '推荐'}"
                }
            })

        except json.JSONDecodeError:
            # If JSON fails, it might be a direct redirect (rare for these specific endpoints but possible)
            if response.history:
                return jsonify({
                    "code": 200,
                    "data": {
                        "url": response.url,
                        "cover": "https://via.placeholder.com/300x500?text=Video",
                        "title": "随机视频"
                    }
                })
            return jsonify({"code": 500, "msg": "Invalid response from video API"}), 500
            
    except Exception as e:
        print(f"Error in get_video: {e}")
        return jsonify({"code": 500, "msg": str(e)}), 500

@app.route('/api/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({"code": 400, "msg": "City is required"}), 400
    
    try:
        # User provided key: qbvOGz9XSuLh7MF3rP7
        url = "https://api.yaohud.cn/api/v6/weather"
        params = {
            "key": "qbvOGz9XSuLh7MF3rP7",
            "location": city
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        try:
            data = response.json()
            return jsonify(data)
        except json.JSONDecodeError:
            return jsonify({"code": 500, "msg": "Invalid JSON response from external API"}), 500
            
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('join')
def handle_join(data):
    username = data.get('username')
    room = data.get('room', 'default_room')
    
    # Add/Update connected user with room info
    connected_users[request.sid] = {'username': username, 'room': room}
    
    join_room(room)
    emit('message', {'user': '系统消息', 'text': f'{username} 已加入房间'}, room=room)
    
    # Broadcast updated user list to the room
    users = get_room_users(room)
    emit('room_users_update', {'room': room, 'users': users, 'count': len(users)}, room=room)

@socketio.on('leave')
def handle_leave(data):
    username = data.get('username')
    room = data.get('room')
    if room:
        leave_room(room)
        # Update connected_users to remove room info or set to None
        if request.sid in connected_users:
            connected_users[request.sid]['room'] = None
            
        emit('message', {'user': '系统消息', 'text': f'{username} 已离开房间'}, room=room)
        
        # Broadcast updated user list to the room
        users = get_room_users(room)
        emit('room_users_update', {'room': room, 'users': users, 'count': len(users)}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data.get('room', 'default_room')
    
    # Save message to database
    # Filter out system messages if they are just notifications (optional, but good practice)
    # Here we save everything that has a user and text
    user = data.get('user')
    text = data.get('text')
    msg_type = data.get('type', 'text')
    
    if user and text and user != '系统消息':
        save_message_db(room, user, text, msg_type)
        
    emit('message', data, room=room)

@socketio.on('disconnect')
def handle_disconnect():
    user_data = connected_users.pop(request.sid, None)
    if user_data:
        username = user_data['username']
        room = user_data.get('room')
        
        print(f'Client disconnected: {username} from room {room}')
        
        if room:
            # Notify room that user left
            emit('message', {'user': '系统消息', 'text': f'{username} 已离开房间'}, room=room)
            # Update user list in room
            users = get_room_users(room)
            emit('room_users_update', {'room': room, 'users': users, 'count': len(users)}, room=room)
    else:
        print('Client disconnected')

if __name__ == '__main__':
    init_db()
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
