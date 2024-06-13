import zmq
import json
import zlib
import gpt4_interface

def start_server(host='192.168.123.42', port=12345):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://{host}:{port}")
    print(f"Server listening on {host}:{port}")

    while True:
        compressed_data = socket.recv()
        decompressed_data = zlib.decompress(compressed_data).decode('utf-8')
        message_history = json.loads(decompressed_data)

        response = gpt4_interface.query_gpt4v(text=None, image=None, message_history=message_history)
        response_dict = {'response': response}
        response_json = json.dumps(response_dict).encode('utf-8')
        compressed_response = zlib.compress(response_json)
        socket.send(compressed_response)

if __name__ == '__main__':
    start_server()
