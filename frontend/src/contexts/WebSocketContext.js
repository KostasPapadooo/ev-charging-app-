import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

const WebSocketContext = createContext();

export const useWebSocket = () => {
    const context = useContext(WebSocketContext);
    if (!context) {
        throw new Error('useWebSocket must be used within a WebSocketProvider');
    }
    return context;
};

export const WebSocketProvider = ({ children }) => {
    const [socket, setSocket] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('disconnected');

    // Event listeners map
    const [eventListeners, setEventListeners] = useState(new Map());

    const connect = useCallback(() => {
        if (socket?.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }

        console.log('🔗 Connecting to WebSocket...');
        setConnectionStatus('connecting');

        const ws = new WebSocket('ws://localhost:8000/ws');

        ws.onopen = () => {
            console.log('✅ WebSocket connected');
            setIsConnected(true);
            setConnectionStatus('connected');
            setSocket(ws);
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                console.log('📨 WebSocket message received:', message);
                
                setLastMessage(message);

                // Call registered event listeners
                const listeners = eventListeners.get(message.type) || [];
                listeners.forEach(callback => {
                    try {
                        callback(message.data);
                    } catch (error) {
                        console.error('Error in WebSocket event listener:', error);
                    }
                });

            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.onclose = (event) => {
            console.log('🔌 WebSocket disconnected:', event.code, event.reason);
            setIsConnected(false);
            setConnectionStatus('disconnected');
            setSocket(null);

            // Attempt to reconnect after 3 seconds
            if (event.code !== 1000) { // Not a normal closure
                setTimeout(() => {
                    console.log('🔄 Attempting to reconnect...');
                    connect();
                }, 3000);
            }
        };

        ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            setConnectionStatus('error');
        };

    }, [eventListeners]);

    const disconnect = useCallback(() => {
        if (socket) {
            console.log('🔌 Disconnecting WebSocket...');
            socket.close(1000, 'User requested disconnect');
            setSocket(null);
            setIsConnected(false);
            setConnectionStatus('disconnected');
        }
    }, [socket]);

    const sendMessage = useCallback((message) => {
        if (socket?.readyState === WebSocket.OPEN) {
            const messageStr = JSON.stringify(message);
            socket.send(messageStr);
            console.log('📤 WebSocket message sent:', message);
        } else {
            console.warn('⚠️ WebSocket not connected, cannot send message');
        }
    }, [socket]);

    // Subscribe to specific message types
    const addEventListener = useCallback((eventType, callback) => {
        setEventListeners(prev => {
            const newMap = new Map(prev);
            const listeners = newMap.get(eventType) || [];
            listeners.push(callback);
            newMap.set(eventType, listeners);
            return newMap;
        });

        // Return cleanup function
        return () => {
            setEventListeners(prev => {
                const newMap = new Map(prev);
                const listeners = newMap.get(eventType) || [];
                const index = listeners.indexOf(callback);
                if (index > -1) {
                    listeners.splice(index, 1);
                    if (listeners.length === 0) {
                        newMap.delete(eventType);
                    } else {
                        newMap.set(eventType, listeners);
                    }
                }
                return newMap;
            });
        };
    }, []);

    // Request immediate station update
    const requestStationUpdate = useCallback(() => {
        sendMessage({
            type: 'request_update',
            timestamp: new Date().toISOString()
        });
    }, [sendMessage]);

    // Send ping to keep connection alive
    const ping = useCallback(() => {
        sendMessage({
            type: 'ping',
            timestamp: new Date().toISOString()
        });
    }, [sendMessage]);

    // Auto-connect on mount
    useEffect(() => {
        connect();
        return () => {
            disconnect();
        };
    }, [connect, disconnect]);

    // Keep-alive ping every 30 seconds
    useEffect(() => {
        if (!isConnected) return;

        const interval = setInterval(ping, 30000);
        return () => clearInterval(interval);
    }, [isConnected, ping]);

    const value = {
        socket,
        isConnected,
        connectionStatus,
        lastMessage,
        connect,
        disconnect,
        sendMessage,
        addEventListener,
        requestStationUpdate,
        ping
    };

    return (
        <WebSocketContext.Provider value={value}>
            {children}
        </WebSocketContext.Provider>
    );
};

export default WebSocketContext; 