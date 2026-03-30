<template>
  <div class="heatmap-wrap">
    <div class="heatmap-scroll">
      <div ref="chartRef" class="heatmap-canvas" :style="chartStyle" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'

type MatrixData = Record<string, Record<string, number>>

interface Props {
  matrix: MatrixData
  min: number
  max: number
  scale?: number
  labelFormatter?: (value: number) => string
  tooltipFormatter?: (value: number) => string
  colors?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  scale: 1,
  labelFormatter: (value: number) => value.toFixed(2),
  tooltipFormatter: (value: number) => value.toFixed(4),
  colors: () => ['#2f5fa7', '#85aee2', '#f6f8fb', '#f0b2a2', '#c23b31']
})

const chartRef = ref<HTMLDivElement | null>(null)
let chart: ECharts | null = null
let resizeObserver: ResizeObserver | null = null

const axisLabels = computed(() => Object.keys(props.matrix))
const scaleFactor = computed(() => Math.max(0.6, props.scale))
const baseChartWidth = computed(() => Math.max(760, axisLabels.value.length * 78 + 140))
const baseChartHeight = computed(() => Math.max(520, axisLabels.value.length * 42 + 180))
const chartWidth = computed(() => Math.round(baseChartWidth.value * scaleFactor.value))
const chartHeight = computed(() => Math.round(baseChartHeight.value * scaleFactor.value))
const chartStyle = computed(() => ({
  width: `${chartWidth.value}px`,
  height: `${chartHeight.value}px`
}))

function buildOption(matrix: MatrixData): EChartsOption {
  const xLabels = Object.keys(matrix)
  const yLabels = xLabels.slice()

  const data = yLabels.flatMap((rowLabel, yIndex) =>
    xLabels.map((columnLabel, xIndex) => {
      const rawValue = matrix[columnLabel]?.[rowLabel]
      const value = Number.isFinite(rawValue) ? rawValue : 0
      return [xIndex, yIndex, value]
    })
  )

  return {
    tooltip: {
      position: 'top',
      formatter: (params: any) => {
        const [xIndex, yIndex, value] = (params?.data as [number, number, number] | undefined) ?? [0, 0, 0]
        return `${yLabels[yIndex]} / ${xLabels[xIndex]}<br/>${props.tooltipFormatter(value)}`
      }
    },
    grid: {
      top: 24,
      right: 112,
      bottom: 110,
      left: 92
    },
    xAxis: {
      type: 'category',
      data: xLabels,
      splitArea: { show: true },
      axisLabel: {
        interval: 0,
        rotate: 35,
        color: '#5f6b7a'
      },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'category',
      data: yLabels,
      splitArea: { show: true },
      axisLabel: {
        interval: 0,
        color: '#5f6b7a'
      },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    visualMap: {
      min: props.min,
      max: props.max,
      calculable: true,
      orient: 'vertical',
      right: 20,
      top: 'middle',
      textStyle: {
        color: '#5f6b7a'
      },
      inRange: {
        color: props.colors
      }
    },
    series: [
      {
        type: 'heatmap',
        data,
        label: {
          show: true,
          color: '#162033',
          formatter: (params: any) => {
            const [, , value] = (params?.data as [number, number, number] | undefined) ?? [0, 0, 0]
            return props.labelFormatter(value)
          }
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 12,
            shadowColor: 'rgba(19, 32, 51, 0.18)'
          }
        }
      }
    ]
  }
}

async function renderChart() {
  if (!chartRef.value) {
    return
  }

  await nextTick()

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  chart.setOption(buildOption(props.matrix), true)
  chart.resize()
}

onMounted(() => {
  void renderChart()

  if (chartRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      chart?.resize()
    })
    resizeObserver.observe(chartRef.value)
  }
})

watch(
  () => [props.matrix, props.min, props.max, props.colors, props.scale],
  () => {
    void renderChart()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.heatmap-wrap {
  width: 100%;
}

.heatmap-scroll {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}

.heatmap-canvas {
  min-width: 100%;
}
</style>
