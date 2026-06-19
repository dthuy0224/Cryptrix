'use client';

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Layers, 
  Zap, 
  Activity, 
  MessageSquare, 
  Globe, 
  Bell,
  RefreshCw,
  Cpu,
  Database,
  BarChart3
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useWebSocket } from '@/hooks/useWebSocket';
import { MarketTicker, PredictionResult, WhaleAlert, SentimentScore } from '@/types';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  LineChart, 
  Line 
} from 'recharts';

// --- MOCK STARTER DATA ---
const INITIAL_TICKERS: MarketTicker[] = [
  { symbol: 'BTC', price: 68425.50, change24h: 3.42, volume24h: 28450120500, high24h: 69120.00, low24h: 66150.00, timestamp: new Date().toISOString() },
  { symbol: 'ETH', price: 3842.15, change24h: -1.15, volume24h: 15420950300, high24h: 3950.00, low24h: 3790.00, timestamp: new Date().toISOString() },
  { symbol: 'SOL', price: 148.80, change24h: 8.65, volume24h: 4210450900, high24h: 152.40, low24h: 135.20, timestamp: new Date().toISOString() }
];

const INITIAL_PREDICTIONS: PredictionResult[] = [
  { symbol: 'BTC', currentPrice: 68425.50, predictedPrice: 71200.00, direction: 'bullish', confidence: 0.89, modelName: 'XGBoost v2.1-Classifier', horizon: '24h', timestamp: new Date().toISOString() },
  { symbol: 'ETH', currentPrice: 3842.15, predictedPrice: 3780.00, direction: 'bearish', confidence: 0.64, modelName: 'Prophet v1.4-Regressor', horizon: '24h', timestamp: new Date().toISOString() },
  { symbol: 'SOL', price: 148.80, currentPrice: 148.80, predictedPrice: 162.50, direction: 'bullish', confidence: 0.78, modelName: 'LSTM-DeepNeuralNet', horizon: '24h', timestamp: new Date().toISOString() }
];

const INITIAL_SENTIMENTS: SentimentScore[] = [
  { symbol: 'BTC', sentimentScore: 0.62, sentimentLabel: 'positive', mentionCount: 14250, sourceBreakdown: { reddit: 8400, twitter: 5200, news: 650 }, timestamp: new Date().toISOString() },
  { symbol: 'ETH', sentimentScore: 0.15, sentimentLabel: 'neutral', mentionCount: 9240, sourceBreakdown: { reddit: 5100, twitter: 3800, news: 340 }, timestamp: new Date().toISOString() }
];

const INITIAL_WHALES: WhaleAlert[] = [
  { id: '1', blockchain: 'Ethereum', symbol: 'ETH', amount: 4500, amountUsd: 17289675, fromAddress: '0x742d35Cc...8d90', toAddress: 'Binance Cold Wallet', transactionType: 'exchange_in', timestamp: new Date(Date.now() - 1000 * 60 * 4).toISOString() },
  { id: '2', blockchain: 'Bitcoin', symbol: 'BTC', amount: 150, amountUsd: 10263825, fromAddress: 'Unknown Wallet', toAddress: 'Unknown Wallet', transactionType: 'transfer', timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString() }
];

const CHART_HISTORY = [
  { time: '16:00', price: 67100, predicted: 67200 },
  { time: '17:00', price: 67350, predicted: 67300 },
  { time: '18:00', price: 67200, predicted: 67450 },
  { time: '19:00', price: 67800, predicted: 67700 },
  { time: '20:00', price: 67950, predicted: 68100 },
  { time: '21:00', price: 68200, predicted: 68250 },
  { time: '22:00', price: 68425, predicted: 68900 }
];

export default function Home() {
  const [tickers, setTickers] = useState<MarketTicker[]>(INITIAL_TICKERS);
  const [predictions, setPredictions] = useState<PredictionResult[]>(INITIAL_PREDICTIONS);
  const [sentiments, setSentiments] = useState<SentimentScore[]>(INITIAL_SENTIMENTS);
  const [whales, setWhales] = useState<WhaleAlert[]>(INITIAL_WHALES);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'predictions' | 'settings'>('dashboard');

  // WebSocket Integration Setup (Taps Backend FastAPI Stream)
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/market/ws';
  const { isConnected } = useWebSocket<{
    type: string;
    data: any;
  }>(wsUrl, {
    onMessage: (message) => {
      if (message.type === 'ticker') {
        setTickers(prev => prev.map(t => t.symbol === message.data.symbol ? message.data : t));
      } else if (message.type === 'prediction') {
        setPredictions(prev => [message.data, ...prev.slice(0, 4)]);
      } else if (message.type === 'whale') {
        setWhales(prev => [message.data, ...prev.slice(0, 9)]);
      } else if (message.type === 'sentiment') {
        setSentiments(prev => prev.map(s => s.symbol === message.data.symbol ? message.data : s));
      }
    }
  });

  // Simulated live ticks for local visual showcase
  useEffect(() => {
    if (isConnected) return; // Ignore simulation if active socket is live

    const interval = setInterval(() => {
      setTickers(prev => prev.map(ticker => {
        const rand = (Math.random() - 0.495) * 0.005; // Slightly upwards bias
        const nextPrice = ticker.price * (1 + rand);
        const nextChange = ticker.change24h + rand * 100;
        return {
          ...ticker,
          price: parseFloat(nextPrice.toFixed(2)),
          change24h: parseFloat(nextChange.toFixed(2)),
          timestamp: new Date().toISOString()
        };
      }));
    }, 4000);

    return () => clearInterval(interval);
  }, [isConnected]);

  return (
    <div className="min-h-screen bg-[#040612] text-slate-100 flex flex-col selection:bg-violet-500/30 selection:text-white">
      {/* Background ambient glowing nodes */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-violet-600/10 rounded-full blur-[120px] pointer-events-none -z-10 animate-pulse-slow" />
      <div className="absolute bottom-10 right-1/4 w-[400px] h-[400px] bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none -z-10" />

      {/* --- HEADER --- */}
      <header className="sticky top-0 z-40 border-b border-white/5 glass-panel px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-600 shadow-lg shadow-violet-950/50">
            <Layers className="h-6 w-6 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-white bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              CRYPTRIX
            </span>
            <span className="hidden sm:inline-block ml-2 text-xs font-semibold bg-violet-500/10 border border-violet-500/20 text-violet-400 px-2 py-0.5 rounded">
              v0.1-Enterprise
            </span>
          </div>
        </div>

        {/* WebSocket Realtime Sync Indicator */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <span className={`relative flex h-2 w-2`}>
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-amber-400'} opacity-75`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isConnected ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
            </span>
            <span className="text-xs font-medium text-slate-400">
              {isConnected ? 'LIVE SYNCED' : 'DEMO EMULATED'}
            </span>
          </div>
          <Button variant="outline" size="sm" className="hidden md:flex space-x-2 border-slate-800">
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Force Sync</span>
          </Button>
        </div>
      </header>

      {/* --- MAIN PAGE CONTENT --- */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        
        {/* --- DYNAMIC STATS OVERVIEW --- */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {tickers.map(ticker => {
            const isBullish = ticker.change24h >= 0;
            return (
              <Card key={ticker.symbol}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      <div className="h-8 w-8 rounded-lg bg-slate-800 flex items-center justify-center font-bold text-white">
                        {ticker.symbol}
                      </div>
                      <div>
                        <div className="font-semibold text-white">{ticker.symbol} / USDT</div>
                        <div className="text-[10px] text-slate-500">24h Ticker</div>
                      </div>
                    </div>
                    <Badge variant={isBullish ? 'success' : 'danger'}>
                      {isBullish ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                      {isBullish ? '+' : ''}{ticker.change24h}%
                    </Badge>
                  </div>
                  
                  <div className="flex items-baseline space-x-2">
                    <span className="text-2xl font-bold tracking-tight text-white">
                      ${ticker.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                    <span className="text-[10px] text-slate-500">USD</span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-white/5 text-xs">
                    <div>
                      <span className="text-slate-500 block">24h High</span>
                      <span className="text-slate-300 font-medium">${ticker.high24h.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">24h Vol</span>
                      <span className="text-slate-300 font-medium">${(ticker.volume24h / 1e9).toFixed(2)}B</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </section>

        {/* --- DETAILED ANALYTICS CHART & AI ENGINE PANEL --- */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Realtime Chart Panel */}
          <Card className="lg:col-span-2 flex flex-col justify-between">
            <CardHeader className="flex flex-row items-center justify-between pb-0">
              <div>
                <CardTitle>Realtime Prediction Stream</CardTitle>
                <CardDescription>Targeting BTC/USDT with ML-based 24h predictions overlays</CardDescription>
              </div>
              <div className="flex space-x-2 bg-slate-800/40 p-0.5 border border-white/5 rounded-lg">
                <Button variant="ghost" size="sm" className="px-3 py-1 h-7 text-xs bg-slate-800 text-white">1H</Button>
                <Button variant="ghost" size="sm" className="px-3 py-1 h-7 text-xs">24H</Button>
                <Button variant="ghost" size="sm" className="px-3 py-1 h-7 text-xs">7D</Button>
              </div>
            </CardHeader>
            <CardContent className="h-[320px] w-full pt-6">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={CHART_HISTORY} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" stroke="#475569" fontSize={11} tickLine={false} />
                  <YAxis domain={['auto', 'auto']} stroke="#475569" fontSize={11} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0d1025', borderColor: '#1e293b', color: '#f1f5f9' }}
                    labelStyle={{ color: '#94a3b8', fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="price" name="Actual Price" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorPrice)" />
                  <Area type="monotone" dataKey="predicted" name="AI Forecast" stroke="#10b981" strokeDasharray="3 3" strokeWidth={1.5} fillOpacity={1} fill="url(#colorPredicted)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* AI Predict Engine Status Widget */}
          <Card className="flex flex-col justify-between">
            <CardHeader>
              <div className="flex items-center space-x-2 text-violet-400 mb-1">
                <Cpu className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-wider">Prediction Engine</span>
              </div>
              <CardTitle>AI Inference Signals</CardTitle>
              <CardDescription>Realtime classification & trend alerts</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {predictions.map(pred => {
                const isBull = pred.direction === 'bullish';
                return (
                  <div key={pred.symbol} className="p-3 bg-white/[0.02] border border-white/5 rounded-lg flex items-center justify-between">
                    <div>
                      <div className="font-bold text-white flex items-center">
                        {pred.symbol}
                        <span className="ml-2 font-normal text-[10px] text-slate-500">[{pred.horizon}]</span>
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5 truncate max-w-[140px]" title={pred.modelName}>
                        {pred.modelName}
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <Badge variant={isBull ? 'success' : 'danger'}>
                        {isBull ? 'BULLISH' : 'BEARISH'}
                      </Badge>
                      <div className="text-[10px] text-slate-400 mt-1">
                        Conf: {(pred.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </section>

        {/* --- SOCIAL SENTIMENT & WHALE ALERTS --- */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Social Media Sentiment Index */}
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2 text-indigo-400 mb-1">
                <MessageSquare className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-wider">Social Sentiment Index</span>
              </div>
              <CardTitle>Realtime Community Pulse</CardTitle>
              <CardDescription>NLP analysis compiled from Twitter/X, Reddit, & news streams</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {sentiments.map(sentiment => {
                const pct = ((sentiment.sentimentScore + 1) / 2) * 100; // Map -1/1 to 0%/100%
                return (
                  <div key={sentiment.symbol} className="space-y-2">
                    <div className="flex justify-between items-center text-sm">
                      <span className="font-bold text-white">{sentiment.symbol} Sentiment</span>
                      <span className="text-slate-400 font-medium">
                        {(sentiment.sentimentScore * 100).toFixed(0)}% ({sentiment.sentimentLabel.toUpperCase()})
                      </span>
                    </div>
                    {/* The visual thermometer */}
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-500 bg-gradient-to-r ${sentiment.sentimentScore > 0 ? 'from-indigo-600 to-emerald-500' : 'from-rose-500 to-amber-500'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-500">
                      <span>Twitter: {sentiment.sourceBreakdown.twitter} mentions</span>
                      <span>Reddit: {sentiment.sourceBreakdown.reddit} mentions</span>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Realtime Whale Transfer Stream */}
          <Card className="flex flex-col justify-between">
            <CardHeader>
              <div className="flex items-center space-x-2 text-rose-400 mb-1">
                <Bell className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-wider">Whale Radar</span>
              </div>
              <CardTitle>On-chain Whale Alerts</CardTitle>
              <CardDescription>Large transaction trackers ($10M+ USD threshold)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 max-h-[220px] overflow-y-auto pr-2 custom-scrollbar">
              {whales.map(whale => (
                <div key={whale.id} className="flex justify-between items-center text-xs p-2.5 bg-white/[0.01] border border-white/5 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${whale.transactionType === 'exchange_in' ? 'bg-rose-500' : 'bg-emerald-500'}`} />
                    <div>
                      <span className="font-semibold text-white">
                        {whale.amount.toLocaleString()} {whale.symbol}
                      </span>
                      <span className="text-slate-500 block text-[10px]">
                        {whale.transactionType === 'exchange_in' ? 'Deposit to Exchange' : 'Transfer to Wallet'}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-300 block font-medium">
                      ${(whale.amountUsd / 1e6).toFixed(2)}M USD
                    </span>
                    <span className="text-slate-500 block text-[9px]">{whale.blockchain}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </section>

      </main>

      {/* --- FOOTER PLATFORM TELEMETRY --- */}
      <footer className="mt-auto border-t border-white/5 bg-[#03040c] py-6 px-8 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center space-x-2">
            <Database className="h-3.5 w-3.5 text-slate-500" />
            <span>Infra: BigQuery + GCS Lakehouse</span>
            <span className="text-slate-800">|</span>
            <Activity className="h-3.5 w-3.5 text-slate-500" />
            <span>Orchestration: Apache Airflow</span>
          </div>
          <div>
            &copy; 2026 Cryptrix Inc. Production Grade Enterprise Architecture Sandbox.
          </div>
        </div>
      </footer>
    </div>
  );
}
