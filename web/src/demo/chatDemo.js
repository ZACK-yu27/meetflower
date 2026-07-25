// P-chat 仿抖音聊天页演示数据（预置消息与模拟消息集中管理，§10）
export const chatDemo = {
  // 预置消息流（2–4 条，评委进入即可看到聊天叙事）
  preset: [
    { from: 'ta', type: 'text', text: '今天路过看到一片向日葵，好好看' },
    { from: 'me', type: 'text', text: '拍下来啦，已经种进我们的花园 🌻' },
    { from: 'ta', type: 'text', text: '好耶，这次我们一起把它养到开花' }
  ],
  // 模拟器点击后追加的模拟消息（§3 P-chat 互动反馈）
  simulated: {
    // 互发消息 = 左右各一条文本泡
    mutual_message: [
      { from: 'ta', type: 'text', text: '在干嘛呀，记得给花儿浇水哦' },
      { from: 'me', type: 'text', text: '刚浇完，它长得可好了 🌱' }
    ],
    // 分享视频 = 视频卡泡（归属按接口 description 区分：你分享=右泡 / TA 分享=左泡）
    share_video: { type: 'video', caption: '分享视频' },
    // 延续互动 = 居中系统灰条
    streak: { type: 'system', text: '你们已连续互动 3 天' }
  }
}
