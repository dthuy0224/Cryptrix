export interface MarketTicker {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  timestamp: string;
}

export interface PredictionResult {
  symbol: string;
  currentPrice: number;
  predictedPrice: number;
  direction: 'bullish' | 'bearish' | 'neutral';
  confidence: number; // 0.0 to 1.0
  modelName: string;
  horizon: string; // e.g. "1h", "24h"
  timestamp: string;
}

export interface WhaleAlert {
  id: string;
  blockchain: string;
  symbol: string;
  amount: number;
  amountUsd: number;
  fromAddress: string;
  toAddress: string;
  transactionType: 'transfer' | 'exchange_in' | 'exchange_out';
  timestamp: string;
}

export interface SentimentScore {
  symbol: string;
  sentimentScore: number; // -1.0 (extremely negative) to +1.0 (extremely positive)
  sentimentLabel: 'positive' | 'negative' | 'neutral';
  mentionCount: number;
  sourceBreakdown: {
    reddit: number;
    twitter: number;
    news: number;
  };
  timestamp: string;
}
