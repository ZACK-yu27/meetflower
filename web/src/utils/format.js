// 时间与展示相关的小工具

// 置信度 0.93 -> 93
export function percentNumber(ratio) {
  return Math.round((ratio || 0) * 100)
}

// 成长阶段英文名 -> 中文名（种子→萌芽→幼苗→花苞→盛放）
export const STAGE_NAMES = {
  seed: '种子',
  sprout: '萌芽',
  seedling: '幼苗',
  bud: '花苞',
  bloom: '盛放'
}

export const STAGE_ORDER = ['seed', 'sprout', 'seedling', 'bud', 'bloom']
