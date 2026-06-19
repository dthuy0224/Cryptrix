import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketOptions<T> {
  onMessage?: (data: T) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export function useWebSocket<T>(url: string, options: UseWebSocketOptions<T> = {}) {
  const { onMessage, reconnectAttempts = 5, reconnectInterval = 3000 } = options;
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Event | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
        console.log(`WebSocket connected to ${url}`);
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data) as T;
          if (onMessage) {
            onMessage(parsed);
          }
        } catch (err) {
          console.error("Failed to parse WebSocket message data:", err);
        }
      };

      ws.onerror = (event) => {
        setError(event);
        console.error("WebSocket error observed:", event);
      };

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;
        
        // Attempt reconnection
        if (reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current += 1;
          console.log(`WebSocket disconnected. Reconnecting in ${reconnectInterval}ms (Attempt ${reconnectCountRef.current}/${reconnectAttempts})...`);
          
          reconnectTimerRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else {
          console.warn(`WebSocket connection failed after ${reconnectAttempts} attempts.`);
        }
      };

    } catch (err) {
      console.error("WebSocket initiation error:", err);
      setIsConnected(false);
    }
  }, [url, reconnectAttempts, reconnectInterval, onMessage]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: string | object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      wsRef.current.send(data);
    } else {
      console.warn("WebSocket is not connected. Message not sent.");
    }
  }, []);

  return { isConnected, error, sendMessage };
}
