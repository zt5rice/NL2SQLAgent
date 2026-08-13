import ReactECharts from 'echarts-for-react'
import type { ChartConfig } from '../../types'

interface ChartProps {
  config: ChartConfig
}

export default function Chart({ config }: ChartProps) {
  const { type, title, data } = config

  const baseOption = {
    backgroundColor: 'transparent',
    title: {
      text: title,
      textStyle: { color: '#e2e8f0', fontSize: 14 },
      left: 'center',
    },
    tooltip: {
      trigger: type === 'pie' ? 'item' : 'axis',
      backgroundColor: 'rgba(30, 41, 59, 0.9)',
      borderColor: '#475569',
      textStyle: { color: '#e2e8f0' },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  }

  const names = data.map((d) => d.name)
  const values = data.map((d) => Number(d.value))

  const getOption = () => {
    switch (type) {
      case 'bar':
        return {
          ...baseOption,
          xAxis: {
            type: 'category',
            data: names,
            axisLine: { lineStyle: { color: '#475569' } },
            axisLabel: { color: '#94a3b8' },
          },
          yAxis: {
            type: 'value',
            axisLine: { lineStyle: { color: '#475569' } },
            axisLabel: { color: '#94a3b8' },
            splitLine: { lineStyle: { color: '#334155' } },
          },
          series: [
            {
              type: 'bar',
              data: values,
              itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] },
            },
          ],
        }
      case 'line':
        return {
          ...baseOption,
          xAxis: {
            type: 'category',
            data: names,
            axisLine: { lineStyle: { color: '#475569' } },
            axisLabel: { color: '#94a3b8' },
          },
          yAxis: {
            type: 'value',
            axisLine: { lineStyle: { color: '#475569' } },
            axisLabel: { color: '#94a3b8' },
            splitLine: { lineStyle: { color: '#334155' } },
          },
          series: [
            {
              type: 'line',
              data: values,
              smooth: true,
              lineStyle: { color: '#3b82f6', width: 2 },
              itemStyle: { color: '#3b82f6' },
            },
          ],
        }
      case 'pie':
        return {
          ...baseOption,
          series: [
            {
              type: 'pie',
              radius: ['40%', '70%'],
              center: ['50%', '55%'],
              data: data.map((d) => ({ name: d.name, value: Number(d.value) })),
              label: { color: '#94a3b8' },
              itemStyle: { borderColor: '#1e293b', borderWidth: 2 },
            },
          ],
        }
      default:
        return baseOption
    }
  }

  return <ReactECharts option={getOption()} style={{ height: '100%', width: '100%' }} notMerge />
}
