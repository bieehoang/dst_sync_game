import wavelink

async def handle_socket(payload):
    await wavelink.Pool.process_socket_response(payload)
