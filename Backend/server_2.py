
import asyncio
import websockets
import json

USERS = set()
NAMES = set()
USERS_NAMES = dict()

def private_message_event(message,sender):
    return json.dumps({"type": "PRIVATE", "message": "%s (mensagem privada) >> %s"%(sender,message)})

def no_user_warning_event():
    message = "Não encontramos esse usuário, verifique se ele está conectado."
    return json.dumps({"type": "SYSTEM", "message": message})

def public_message_event(message,sender):
    return json.dumps({"type": "PUBLIC", "message": "%s >> %s"%(sender,message)})

def hi_event(user):
    return json.dumps({"type": "SYSTEM", "message": "%s entrou na sala."%(user)})

def bye_event(user):
    return json.dumps({"type": "SYSTEM", "message": "%s saiu da sala."%(user)})

def greetings_message_event():
    message = "Por favor insira seu nome. (ex: /name SeuNome)"
    return json.dumps({"type": "SYSTEM", "message": message})

def retry_name_message_event():
    message = "Alguém já esta usando esse nome, por favor insira outro nome."
    return json.dumps({"type": "SYSTEM", "message": message})

def name_first_event():
    message = "Por favor, insira seu nome primeiro. (ex: /name SeuNome)"
    return json.dumps({"type": "SYSTEM", "message": message})

def got_in_event(user):
    message = "Nomes estabelecido com sucesso! Seu nome é %s"%(user)
    return json.dumps({"type": "SYSTEM", "message": message})

##########################################################################################################

async def private_message(connection, message, receiver):
    if USERS:  # asyncio.wait doesn't accept an empty list
        
        receiver_connection = None
        for conn, name in USERS_NAMES.items():
            if name == receiver:
                receiver_connection = conn
            
        if receiver_connection:
            message = private_message_event(message, USERS_NAMES[connection])
            await receiver_connection.send(message)
        else:
            message = no_user_warning_event()
            await connection.send(message)



async def public_message(connection, message):
    if USERS:  # asyncio.wait doesn't accept an empty list
        message = public_message_event(message,USERS_NAMES[connection])
        for user in USERS:
            if user != connection:
                await user.send(message)


async def enter_room(connection):
    if USERS:
        message = hi_event(USERS_NAMES[connection])
        for user in USERS:
            if user != connection:
                await user.send(message)

async def leave_room(connection):
    if USERS:
        message = bye_event(USERS_NAMES[connection])
        for user in USERS:
            if user != connection:
                await user.send(message)

async def greetings(connection):
    message = greetings_message_event()
    await connection.send(message)


async def name_retry(connection):
    message = retry_name_message_event()
    await connection.send(message)

async def name_first(connection):
    message = name_first_event()
    await connection.send(message)

async def got_in(connection):
    message = got_in_event(USERS_NAMES[connection])
    await connection.send(message)

async def register(connection):
    await greetings(connection)
    while True:
        json_msg = await connection.recv()
        name_aux = json.loads(json_msg)["message"]
        if name_aux.startswith("/name "):
            name = name_aux[6:]
            if name not in NAMES:
                break
            else:
                message = retry_name_message_event()
                await connection.send(message)
        else:
            message = name_first_event()
            await connection.send(message)
    
    USERS.add(connection)
    NAMES.add(name)
    USERS_NAMES[connection] = name
    await enter_room(connection)
    await got_in(connection)

async def unregister(connection):
    USERS.remove(connection)
    NAMES.remove(USERS_NAMES[connection])
    await leave_room(connection)

async def main(connection, path):
    await register(connection)
    try:
        async for message in connection:
            data = json.loads(message)
            if data["action"] == "public_message":
                await public_message(connection, data["message"])
            elif data["action"] == "private_message":
                await private_message(connection, data['message'], data['receiver'])
    except:
        await unregister(connection)



start_server = websockets.serve(main, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()