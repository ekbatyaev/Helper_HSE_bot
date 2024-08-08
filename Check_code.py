import datetime
#log start
current_data = datetime.date.today()
current_time = datetime.datetime.now().time()
print(str(message.from_user.id) +"-" + "Date: " + str(current_data) + " Time: " + str(current_time) + "\n" + message.text)
#log end