import asyncio
import logging
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

# class VideoCallConsumer(AsyncWebsocketConsumer):
#     # Class variable to track rooms and their peers
#     rooms = {}
    
#     async def connect(self):
#         self.room_id = self.scope['url_route']['kwargs']['room_id']
#         self.room_group_name = f'video_call_{self.room_id}'

#         # Initialize room if it doesn't exist
#         if self.room_group_name not in self.rooms:
#             self.rooms[self.room_group_name] = set()

#         # Add the new peer to the room
#         self.rooms[self.room_group_name].add(self.channel_name)
        
#         # Check if this is the first peer (initiator)
#         is_initiator = len(self.rooms[self.room_group_name]) == 1

#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )
#         await self.accept()

#         # Send join response with initiator status
#         await self.send(text_data=json.dumps({
#             'type': 'join_response',
#             'is_initiator': is_initiator,
#             'peers_in_room': len(self.rooms[self.room_group_name])
#         }))

#         print(f"Peer connected to room {self.room_id}. Is initiator: {is_initiator}")
#         print(f"Total peers in room: {len(self.rooms[self.room_group_name])}")

#     async def disconnect(self, close_code):
#         # Remove peer from room
#         if self.room_group_name in self.rooms:
#             self.rooms[self.room_group_name].remove(self.channel_name)
            
#             # Clean up empty rooms
#             if not self.rooms[self.room_group_name]:
#                 del self.rooms[self.room_group_name]

#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#         print(f"Peer disconnected from room {self.room_id}")
#         if self.room_group_name in self.rooms:
#             print(f"Remaining peers in room: {len(self.rooms[self.room_group_name])}")

#     async def receive(self, text_data):
#         try:
#             data = json.loads(text_data)
#             message_type = data.get('type')
            
#             print(f"Received message type: {message_type} in room {self.room_id}")

#             # Add additional information to the message
#             data['room_id'] = self.room_id
            
#             # Relay message to all peers in the room except the sender
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'relay_message',
#                     'message': data,
#                     'sender_channel_name': self.channel_name
#                 }
#             )
#         except json.JSONDecodeError as e:
#             print(f"Error decoding message: {e}")
#         except Exception as e:
#             print(f"Error processing message: {e}")

#     async def relay_message(self, event):
#         message = event['message']
#         sender_channel_name = event['sender_channel_name']

#         # Don't send the message back to the sender
#         if sender_channel_name != self.channel_name:
#             await self.send(text_data=json.dumps(message))
#             print(f"Relayed {message['type']} message to peer in room {self.room_id}")
#     async def connect(self):
#         self.room_id = self.scope['url_route']['kwargs']['room_id']
#         self.room_group_name = f'video_call_{self.room_id}'

#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )
#         await self.accept()

logger = logging.getLogger(__name__)

import logging
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

class VideoCallConsumer(AsyncWebsocketConsumer):
    rooms = {}  # Track rooms and their connected peers
    
    async def connect(self):
        # Extract room information
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'video_call_{self.room_id}'

        # Initialize room if it doesn't exist
        if self.room_id not in VideoCallConsumer.rooms:
            VideoCallConsumer.rooms[self.room_id] = set()

        # Add this connection to the room
        VideoCallConsumer.rooms[self.room_id].add(self.channel_name)

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

        # Determine if this is the initiator (first peer)
        is_initiator = len(VideoCallConsumer.rooms[self.room_id]) == 1


        logger.info(f"Peer connected to room {self.room_id}. Initiator: {is_initiator}. Total peers: {len(VideoCallConsumer.rooms[self.room_id])}")
        

        # Notify peers when a second peer joins
        if len(VideoCallConsumer.rooms[self.room_id]) == 2:
            for peer in VideoCallConsumer.rooms[self.room_id]:
                if peer != self.channel_name:
                    await self.channel_layer.send(peer, {
                        'type': 'peer_joined',
                        'message': {'type': 'peer_joined'}
                    })

        # Send join response to the current peer
        await self.send(text_data=json.dumps({
            'type': 'join_response',
            'is_initiator': is_initiator,
            'peers_count': len(VideoCallConsumer.rooms[self.room_id])
        }))

    async def disconnect(self, close_code):
        # Remove the current peer from the room
        if self.room_id in VideoCallConsumer.rooms:
            VideoCallConsumer.rooms[self.room_id].remove(self.channel_name)

            # Clean up room if empty
            if not VideoCallConsumer.rooms[self.room_id]:
                del VideoCallConsumer.rooms[self.room_id]

        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        logger.info(f"Peer disconnected from room {self.room_id}. Remaining peers: {len(VideoCallConsumer.rooms.get(self.room_id, []))}")

    async def receive(self, text_data):
        try:
            # Parse the incoming message
            data = json.loads(text_data)
            message_type = data.get('type')
            logger.info(f"Received message type {message_type} in room {self.room_id}")

            # Relay messages only if there are at least two peers
            if len(VideoCallConsumer.rooms[self.room_id]) > 1:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'relay_message',
                        'message': data,
                        'sender': self.channel_name
                    }
                )
            else:
                logger.warning(f"Attempted SDP/ICE exchange with less than two peers in room {self.room_id}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def relay_message(self, event):
        # Relay message to peers, excluding the sender
        message = event['message']
        sender = event['sender']

        if sender != self.channel_name:
            try:
                await self.send(text_data=json.dumps(message))
                logger.info(f"Relayed {message.get('type')} message in room {self.room_id}")
            except Exception as e:
                logger.error(f"Error relaying message: {e}")

    async def peer_joined(self, event):
        # Notify the initiator that a second peer has joined
        await self.send(text_data=json.dumps(event['message']))

    rooms = {}
    
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'video_call_{self.room_id}'

        # Initialize room if it doesn't exist
        if self.room_id not in VideoCallConsumer.rooms:
            VideoCallConsumer.rooms[self.room_id] = set()

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Add to room after accepting
        VideoCallConsumer.rooms[self.room_id].add(self.channel_name)
        
        # Determine if this is the initiator (first peer)
        is_initiator = len(VideoCallConsumer.rooms[self.room_id]) == 1
        
        logger.info(f"New peer connected to room {self.room_id}. Total peers: {len(VideoCallConsumer.rooms[self.room_id])}")
        
        # Send join response
        await self.send(text_data=json.dumps({
            'type': 'join_response',
            'is_initiator': is_initiator,
            'peers_count': len(VideoCallConsumer.rooms[self.room_id])
        }))

    async def disconnect(self, close_code):
        if self.room_id in VideoCallConsumer.rooms:
            VideoCallConsumer.rooms[self.room_id].remove(self.channel_name)
            if not VideoCallConsumer.rooms[self.room_id]:
                del VideoCallConsumer.rooms[self.room_id]
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"Peer disconnected from room {self.room_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            logger.info(f"Received message type {data.get('type')} in room {self.room_id}")
            
            # Forward the message to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'relay_message',
                    'message': data,
                    'sender': self.channel_name
                }
            )
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    async def relay_message(self, event):
        message = event['message']
        sender = event['sender']
        
        # Don't send back to the sender
        if sender != self.channel_name:
            try:
                await self.send(text_data=json.dumps(message))
                logger.info(f"Relayed {message.get('type')} message in room {self.room_id}")
            except Exception as e:
                logger.error(f"Error relaying message: {str(e)}")