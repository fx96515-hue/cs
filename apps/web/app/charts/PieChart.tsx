"use client";

import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface PieChartProps {
  data: Record<string, unknown>[];
  dataKey: string;
  nameKey: string;
  title?: string;
  colors?: string[];
}

const DEFAULT_COLORS = ["#5786ff", "#40d67b", "#ffb740", "#ff5c5c", "#b17fff", "#ff78d4"];

export default function PieChart({
  data,
  dataKey,
  nameKey,
  title,
  colors = DEFAULT_COLORS,
}: PieChartProps) {
  return (
    <div className="chart">
      {title && <div className="chartTitle">{title}</div>}
      <ResponsiveContainer width="100%" height={300}>
        <RechartsPieChart>
          <Pie
            data={data}
            dataKey={dataKey}
            nameKey={nameKey}
            cx="50%"
            cy="50%"
            outerRadius={100}
            label
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "var(--panel)",
              border: "1px solid var(--border)",
              borderRadius: "12px",
            }}
          />
          <Legend />
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
}
