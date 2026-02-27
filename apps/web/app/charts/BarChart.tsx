"use client";

import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface BarChartProps {
  data: any[];
  xKey: string;
  yKey: string;
  title?: string;
  color?: string;
}

export default function BarChart({ data, xKey, yKey, title, color = "#5786ff" }: BarChartProps) {
  return (
    <div className="chart">
      {title && <div className="chartTitle">{title}</div>}
      <ResponsiveContainer width="100%" height={300}>
        <RechartsBarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
          <XAxis dataKey={xKey} stroke="var(--muted)" />
          <YAxis stroke="var(--muted)" />
          <Tooltip
            contentStyle={{
              background: "var(--panel)",
              border: "1px solid var(--border)",
              borderRadius: "12px",
            }}
          />
          <Legend />
          <Bar dataKey={yKey} fill={color} />
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}
