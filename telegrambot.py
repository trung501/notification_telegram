# pip install python-telegram-bot
# pip install python-telegram-bot[job-queue]
from telegram import Update, Bot
from telegram.ext import Application,ApplicationBuilder, CommandHandler, ContextTypes,JobQueue

import time
import datetime
from datetime import  timedelta
import json
import asyncio
import pytz
from config_telegram import TOKEN,weekday_dict,weekday_data

timezone_Hanoi = pytz.timezone('Asia/Ho_Chi_Minh')
token=TOKEN
list_group=[]
def save_data():
    global list_group
    print(list_group)
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

def validate_time(time_receive,format="%Y-%m-%d %H:%M"):
    try:
        time.strptime(time_receive, format)
        return time_receive
    except Exception as e:
        print(e)
        return None
    
def validate_duration(duration):
    try:
        if isinstance(duration, str):
            duration=int(duration)
        if duration>0:
            return duration
        else:
            return None
    except Exception as e:
        print(e)
        return None

def validate_list_week(list_week):
    try:
        print(list_week)
        if type(list_week)==str:
            print("list_week is str")
            list_week = eval(list_week)
        if type(list_week)==list:
            for _week in list_week:
                if _week not in weekday_data.keys():
                    return None
            return list_week            
        return list_week
    except Exception as e:
        print(e)
        return None

def get_next_datetime_from_weekday(weekday:str="Monday",hour=0,minute=0,format="%Y-%m-%d %H:%M"):
    weekday = weekday_dict[weekday]
    today = datetime.datetime.now()
    today_weekday = today.strftime("%A")
    today_weekday = weekday_dict[today_weekday]
    if weekday == today_weekday:
        pass
    else:
        while today_weekday != weekday:
            today = today+timedelta(days=1)
            today_weekday = today.strftime("%A")
            today_weekday = weekday_dict[today_weekday]

    today=today.replace(hour=hour,minute=minute)
    return today.strftime(format)

def get_string_day(_time="'2023-05-07 12:50'",format:str="%Y-%m-%d %H:%M"):
    _time = datetime.datetime.strptime(_time,format)    
    return f"{weekday_dict[str(_time.strftime('%A'))]}, {_time.hour} giờ {_time.minute} phút, {_time.day}/{_time.month}/{_time.year} "

def get_next_id(group):
    max_id =0
    for _message in group["data"]:
        if _message["id"]>max_id:
            max_id=_message["id"]
    return max_id+1

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
    message+="- Tạo thông báo trong tuần: /set_message_week {\"list_week\":\"['T2','T3','CN']\",\"time\":\"20:32\",\"message\":\"Nhắc nhở\"}\n"
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
        duration = validate_duration(json_data.get("duration"))
        time_receive = validate_time(json_data.get("time_receive"),"%Y-%m-%d %H:%M")
        message = json_data.get("message")
        if message is None:
            message=""
        id=json_data.get("id")
        if id is None and duration is not None and time_receive is not None :
            for group in list_group:
                if group["chat_id"]==update.message.chat_id:
                    group["data"].append({"id":get_next_id(group),"time_receive":time_receive,"duration":duration,"message":message})
                    message="Đã cập nhật tin nhắn nhắc nhở"
                    print(group)
                    break
        elif id is not None and duration is not None and time_receive is not None:
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
                        group["data"].append({"id":get_next_id(group),"time_receive":time_receive,"duration":duration,"message":message})
                        message="Đã cập nhật tin nhắn nhắc nhở"
                        print(group)
                    break
        else:
            message="Sai định dạng, vui lòng nhập lại"
    except Exception as e:
        message="Sai định dạng, vui lòng nhập lại"
        print("ERROR:",e)
    save_data()
    await update.message.reply_text(message)

async def set_message_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data=update.message.text
    data=data.replace("/set_message_week","").strip()
    message="Không tìm thấy nhóm này trong danh sách, vui lòng nhập /start để bắt đầu"
    # try:
    if True:
        print(data)
        json_data = json.loads(data)
        list_week=validate_list_week(json_data.get("list_week"))
        message = json_data.get("message")
        if message is None:
            message=""
        _time=validate_time(json_data.get("time"),"%H:%M")
        duration=7
        if list_week is None:
            print("list_week is None")
            message="Sai định dạng, vui lòng nhập lại"
        elif _time is None:
            print("time is None")
            message="Sai định dạng, vui lòng nhập lại"
        else:
            _time = datetime.datetime.strptime(json_data.get("time"),"%H:%M")
            hour=_time.hour
            minute=_time.minute
            for group in list_group:
                if group["chat_id"]==update.message.chat_id:
                    for week in list_week:
                        id = get_next_id(group)
                        week= weekday_data[week].get("EN")
                        time_receive = get_next_datetime_from_weekday(week,hour=hour,minute=minute)
                        group["data"].append({"id":id,"time_receive":time_receive,"duration":duration,"message":message})

                    message="Đã cập nhật tin nhắn nhắc nhở"
                    print(group)
                    break

        

    # except Exception as e:
    #     message="Sai định dạng, vui lòng nhập lại"
    #     print("ERROR:",e)
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
                string_day =get_string_day(_message["time_receive"])
                message+=f"Thời gian nhận:  {string_day}\n"
                message+=f"Thời gian nhận tiếp theo: {_message['duration']} ngày\n"
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
app.add_handler(CommandHandler("set_message_week", set_message_week))
app.run_polling()
