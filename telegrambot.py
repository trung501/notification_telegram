# pip install python-telegram-bot
# pip install python-telegram-bot[job-queue]
from telegram import Update, Bot
from telegram.ext import Application,ApplicationBuilder, CommandHandler, ContextTypes,JobQueue

import time
import datetime
import json
import asyncio
import pytz


timezone_Hanoi = pytz.timezone('Asia/Ho_Chi_Minh')
token=""
list_group=[]
def save_data():
    global list_group
    with open("data.json", "w") as outfile:
        json.dump(list_group, outfile)
    print("Save data success")
def load_data():
    global list_group
    try:
        with open("data.json") as json_file:
            list_group = json.load(json_file)
        print("Load data success")
    except Exception as e:
        print(e)
        list_group=[]

 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Get group id
    chat_id = update.message.chat_id
    json_save={"chat_id":chat_id, "name":update.message.chat.title,"data":[]}
    print(json_save)
    # check group exist
    check=False
    for group in list_group:
        if group["chat_id"]==chat_id:
            check=True
            print(f"Group {update.message.chat.title} exist")
            break
    if check==False:
        list_group.append(json_save)
    message=f"Xin chào {update.effective_user.first_name}, bây giờ tôi sẽ thường xuyên gửi thông báo nhắc nhở qua group {update.message.chat.title} này\n"
    # help
    message+="Các lệnh hỗ trợ:\n"
    message+="- Tạo một thông báo mới: /set_message {\"time_receive\":\"2021-09-30 00:00\",\"duration\":1,\"message\":\"Nhắc nhở\"}\n"
    message+="- Cập nhật thông báo: /set_message {\"id\":1,\"time_receive\":\"2021-09-30 00:00\",\"duration\":1,\"message\":\"Nhắc nhở\"}\n"
    message+="- Xóa thông báo: /delete_message {\"id\":1}\n"
    message+="- Xem danh sách thông báo: /get_message\n"
    #get list job
    check=False
    for job in context.job_queue.jobs():
        if job.name=="auto_send":
            check=True
            print("Job auto_send exist")
            break
    if check==False:
        context.job_queue.run_repeating(send_message,name="auto_send", interval=50, first=0)        
    await update.message.reply_text(message)


async def set_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data=update.message.text
    data=data.replace("/set_message","").strip()
    message="Không tìm thấy nhóm này trong danh sách, vui lòng nhập /start để bắt đầu"
    try:
        print(data)
        json_data = json.loads(data)
        if json_data.get("duration") is None:
            message="Không tìm thấy khoảng thời gian nhận thông báo"
        elif json_data.get("time_receive") is None:
            json_data["time_receive"]=datetime.datetime.now(timezone_Hanoi).strftime("%Y-%m-%d %H:%M")
            message="Không tìm thấy thời gian nhận thông báo"
        elif json_data.get("message") is None:
            message="Không tìm thấy tin nhắn nhắc nhở"
        elif json_data.get("id") is None:
            for group in list_group:
                if group["chat_id"]==update.message.chat_id:
                    # get next id
                    max_id =0
                    for message in group["data"]:
                        if message["id"]>max_id:
                            max_id=message["id"]
                    json_data["id"]=max_id+1
                    group["data"].append({"id":json_data["id"],"time_receive":json_data["time_receive"],"duration":json_data["duration"],"message":json_data["message"]})
                    message="Đã cập nhật tin nhắn nhắc nhở"
                    print(group)
                    break
        elif json_data.get("id") is not None:
            for group in list_group:
                if group["chat_id"]==update.message.chat_id:
                    check=False
                    for _message in group["data"]:
                        if _message["id"]==json_data["id"]:
                            _message["time_receive"]=json_data["time_receive"]
                            _message["duration"]=json_data["duration"]
                            _message["message"]=json_data["message"]
                            message="Đã cập nhật tin nhắn nhắc nhở"
                            print(group)
                            break
                    if check==False:
                        # get next id
                        max_id =0
                        for _message in group["data"]:
                            if _message["id"]>max_id:
                                max_id=_message["id"]
                        json_data["id"]=max_id+1
                        message["data"].append({"id":json_data["id"],"time_receive":json_data["time_receive"],"duration":json_data["duration"],"message":json_data["message"]})                         
                        message="Đã cập nhật tin nhắn nhắc nhở"
                        print(group)
                    break
    except Exception as e:
        print("ERROR:",e)
    save_data()
    await update.message.reply_text(message)

async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message="Không tìm thấy nhóm này trong danh sách, vui lòng nhập /start để bắt đầu"
    for group in list_group:
        if group["chat_id"]==update.message.chat_id:
            message="Danh sách tin nhắn nhắc nhở\n"
            for _message in group["data"]:
                message=message+"*"*20+"\n"
                message+=f"ID: {_message['id']}\n"
                message+=f"Thời gian nhận: {_message['time_receive']}\n"
                message+=f"Khoảng thời gian nhận: {_message['duration']} ngày\n"
                message+=f"Tin nhắn nhắc nhở: {_message['message']}\n"
                message=message+"*"*20+"\n"                
            break
    await update.message.reply_text(message)

async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message="Không tìm thấy nhóm này trong danh sách, vui lòng nhập /start để bắt đầu"
    try:
        data=update.message.text
        data=data.replace("/delete_message","").strip()
        json_data = json.loads(data)
        if json_data.get("id") is None:
            message="Không tìm thấy id tin nhắn nhắc nhở"
        else:
            for group in list_group:
                if group["chat_id"]==update.message.chat_id:
                    for _message in group["data"]:
                        check=False
                        if _message["id"]==json_data["id"]:
                            group["data"].remove(_message)
                            message="Đã xóa tin nhắn nhắc nhở"
                            print(group)
                            check=True
                            break
                    if check==False:
                        message="Không tìm thấy id tin nhắn nhắc nhở"
                    break
        save_data()
    except Exception as e:
        print(e)
    await update.message.reply_text(message)

async def send_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.datetime.now(timezone_Hanoi).strftime("%Y-%m-%d %H:%M")
    print(f"{now} Check and send message")
    bot = Bot(token=token)
    for group in list_group:
        for _message in group["data"]:
            message=f"Nhắc nhở: {_message['message']}\n"
            time_receive = datetime.datetime.strptime(_message["time_receive"], "%Y-%m-%d %H:%M")
            time_receive_aware = timezone_Hanoi.localize(time_receive)
            between_time = abs((datetime.datetime.now(timezone_Hanoi) - time_receive_aware).total_seconds())
            if between_time < 100:
                print(f"between_time: {between_time}")
                await bot.send_message(group["chat_id"], message)
                duration=int(_message["duration"])
                _message["time_receive"]=(time_receive_aware+datetime.timedelta(days=duration)).strftime("%Y-%m-%d %H:%M")
                save_data()
                print(f"send message to {group['chat_id']} success")


load_data()
app =  Application.builder().token(token).build()

app.add_handler(CommandHandler(["start", "help"], start))
app.add_handler(CommandHandler("set_message", set_message))
app.add_handler(CommandHandler("get_message", get_message))
app.add_handler(CommandHandler("delete_message", delete_message))
app.run_polling()
