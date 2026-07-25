`POST https://ark.cn-beijing.volces.com/api/v3/chat/completions`

发送包含文本、图片、视频、音频等模态的消息列表，模型将生成对话中的下一条消息。

<span id=".6Ym05p2D"></span>
## 鉴权

本接口支持鉴权方式如下，详情请参见 [Base URL 及鉴权](https://www.volcengine.com/docs/82379/1298459)。


* 【推荐】API Key 鉴权，请在 [API Key 管理](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) 页面，获取长效 API Key。

* 【可选】Access Key 鉴权，请在 [Access Key 管理](https://console.volcengine.com/iam/keymanage) 页面，获取 Access Key。



---



<span id=".6K-35rGC5Y-C5pWw"></span>
## 请求参数

<span id=".Ym9keS3lj4LmlbA="></span>
### Body 参数


**messages** `object[]` `必选`  |  消息列表

不同模型支持不同类型的消息，如文本、图片、视频、音频等


系统消息 `object`

系统消息，模型需遵循的指令，包括扮演的角色、背景信息等。


**content** `string / object[]` `必选`  |  消息内容

`messages.content`

系统消息的内容，支持纯文本或多模态内容


纯文本 `string`

纯文本内容



多模态内容 `object[]`

多模态内容，支持文本、图片、视频、音频等模态内容。


文本信息 `object`

文本部分，多模态消息中文本模态的部分。


**text** `string` `必选`  |  文本内容

`messages.content.text`

文本模态部分的内容



**type** `string` `必选`  |  类型

`messages.content.type`

内容模态类型，此处固定为 `text`




图片信息 `object`

图片部分


**image_url** `object` `必选`  |  图片内容

`messages.content.image_url`

图片模态的内容。 图片输入支持 **file_id、url** 两个字段，需二选一传入。具体使用请参见 [图片理解说明](https://www.volcengine.com/docs/82379/1362931)


**url** `string` `必选`  |  资源 URL

`messages.content.image_url.url`

发给模型的图片 URL。支持格式如下：


* 图片链接

* 图片的 Base64 编码



**detail** `string`  |  图片解析粒度

`messages.content.image_url.detail`

图片解析粒度。

理解图片的精细度、不同模型默认取值及对应的具体像素区间，参见 [控制图片理解的精细度](https://www.volcengine.com/docs/82379/1362931#bf4d9224)。可选值：`low`、`high`、`xhigh`。



**file_id** `string`  |  文件 ID

`messages.content.image_url.file_id`

文件 ID。


* 文件 ID 是通过 [Files API](https://www.volcengine.com/docs/82379/1870405)上传文件后返回的 id。

* **file_id** 对应的文件类型需要和 **type** 保持一致，且文件状态需要为 **active** 。

* **API Key** 所属项目与 **file_id** 上传时所属项目需保持一致


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">Chat API 支持通过 <strong>file_id</strong> 传入火山引擎 TOS Bucket 中的文件，支持该能力的模型范围如下：</div>



* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-mini 系列：doubao\-seed\-2\-0\-mini\-260428 及后续版本。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-lite 系列：全版本支持。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-pro 系列：全版本支持。</div>




**image_pixel_limit** `object` `默认值 null`  |  图片像素限制

`messages.content.image_url.image_pixel_limit`

输入给模型的图片的像素范围，如不在此范围，图片会被等比例缩放至该范围。


* 生效优先级：高于 **detail** 字段，即同时配置 **detail** 与 **image_pixel_limit** 字段时，生效 **image_pixel_limit** 字段配置。

* 默认生效规则：若未设置 **image_pixel_limit** ，则使用 **detail** 配置的值对应的 **min_pixels** / **max_pixels** 值。


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">图片像素范围需在 [196, 36,000,000]，否则会直接报错。</div>



**max_pixels** `integer`  |  最大像素

`messages.content.image_url.image_pixel_limit.max_pixels`

传入图片最大像素限制，大于此像素则等比例缩小至 `max_pixels` 字段取值以下。若未设置，则取值为 `detail` 配置的值对应的 `max_pixels` 值。

**模型支持** ：


* **doubao\-seed\-1.8 之前的模型** ：最大值 `4014080`

* **doubao\-seed\-1.8、doubao\-seed\-2.0 模型** ：最大值 `9031680`



**min_pixels** `integer`  |  最小像素

`messages.content.image_url.image_pixel_limit.min_pixels`

传入图片最小像素限制，小于此像素则等比例放大至 `min_pixels` 字段取值以上。若未设置，则取值为 `detail` 配置的值对应的 `min_pixels` 值。

**模型支持** ：


* **doubao\-seed\-1.8 之前的模型** ：最小值 `3136`

* **doubao\-seed\-1.8、doubao\-seed\-2.0 模型** ：最小值 `1764`





**type** `string` `必选`  |  类型

`messages.content.type`

内容模态类型，此处固定为 `image_url`




视频信息 `object`

视频部分


**type** `string` `必选`  |  类型

`messages.content.type`

内容模态类型，此处固定为 `video_url`



**video_url** `object` `必选`  |  视频内容

`messages.content.video_url`

视频消息的内容部分。 视频输入支持 **file_id、url** 两个字段，需二选一传入。具体使用请参见 [视频理解说明](https://www.volcengine.com/docs/82379/1895586)


**url** `string` `必选`  |  资源 URL

`messages.content.video_url.url`

发给模型的视频 URL。支持格式如下：


* 视频链接

* 视频的 Base64 编码



**detail** `string`  |  图片解析粒度

`messages.content.video_url.detail`

从视频中提取帧的精细度



**file_id** `string`  |  文件 ID

`messages.content.video_url.file_id`

文件 ID。


* 文件 ID 是通过 [Files API](https://www.volcengine.com/docs/82379/1870405)上传文件后返回的 id。

* **file_id** 对应的文件类型需要和 **type** 保持一致，且文件状态需要为 **active** 。

* **API Key** 所属项目与 **file_id** 上传时所属项目需保持一致


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">Chat API 支持通过 <strong>file_id</strong> 传入火山引擎 TOS Bucket 中的文件，支持该能力的模型范围如下：</div>



* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-mini 系列：doubao\-seed\-2\-0\-mini\-260428 及后续版本。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-lite 系列：全版本支持。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-pro 系列：全版本支持。</div>




**fps** `number` `默认值 1.0`  |  视频帧率

`messages.content.video_url.fps`

抽帧频率，详见 [视频理解](https://www.volcengine.com/docs/82379/1895586)。


* 取值越高，对视频中画面变化越敏感。

* 取值越低，对视频中画面变化越迟钝，但 token 花费少，速度更快。


**取值范围** ：`[0.2, 5]`



**image_pixel_limit** `object`  |  图片像素限制

`messages.content.video_url.image_pixel_limit`

视频抽帧后应用的像素范围限制


**max_pixels** `integer`  |  最大像素

`messages.content.video_url.image_pixel_limit.max_pixels`

提取帧的最大像素限制



**min_pixels** `integer`  |  最小像素

`messages.content.video_url.image_pixel_limit.min_pixels`

提取帧的最小像素限制






音频信息 `object`

音频部分


**input_audio** `object` `必选`  |  音频内容

`messages.content.input_audio`

音频模态的内容。 音频输入支持 **file_id、url、data** 三个字段，需三选一传入。具体使用请参见 [音频理解](https://www.volcengine.com/docs/82379/2377589)

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>



* <div data-tips="true" data-tips-type="warning">文件大小不超过 25 MB。</div>


* <div data-tips="true" data-tips-type="warning">单次请求音频总时长不超过 120 分钟，仅统计纯音频时长，视频内嵌音频不计入统计。</div>


* <div data-tips="true" data-tips-type="warning">详细说明请参见 <a href="https://www.volcengine.com/docs/82379/2377589">音频理解</a>。</div>




**data** `string`  |  音频数据

`messages.content.input_audio.data`

音频内容的 Base64 编码



**file_id** `string`  |  文件 ID

`messages.content.input_audio.file_id`

文件 ID。


* 文件 ID 是通过 [Files API](https://www.volcengine.com/docs/82379/1870405)上传文件后返回的 id。

* **file_id** 对应的文件类型需要和 **type** 保持一致，且文件状态需要为 **active** 。

* **API Key** 所属项目与 **file_id** 上传时所属项目需保持一致


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">Chat API 支持通过 <strong>file_id</strong> 传入火山引擎 TOS Bucket 中的文件，支持该能力的模型范围如下：</div>



* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-mini 系列：doubao\-seed\-2\-0\-mini\-260428 及后续版本。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-lite 系列：全版本支持。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-pro 系列：全版本支持。</div>




**format** `string`  |  音频格式

`messages.content.input_audio.format`

音频格式。当使用 **data** 时，该参数必填。支持的音频格式 `MIME` 类型如下： 纯音频格式：


* mp3：`audio/mpeg`

* wav：`audio/wav`

* aac：`audio/aac`

* m4a：`audio/m4a`

   视频内嵌音频格式：

* mp3：`audio/mpeg`

* wav：`audio/wav`

* aac：`audio/aac`

* m4a：`audio/m4a`

* pcm：`audio/L16`

* ac3：`audio/ac3`

* alac：`audio/m4a`



**url** `string`  |  资源 URL

`messages.content.input_audio.url`

音频内容的 URL




**type** `string` `必选`  |  类型

`messages.content.type`

内容模态类型，此处固定为 `input_audio`




文件信息 `object`

文件部分


**file** `object` `必选`  |  文件内容

`messages.content.file`

文件模态的内容，当前仅支持 PDF 文件。 文件输入支持 **file_id、file_data、file_url** 三个字段，需三选一传入。多模态理解示例见 [文档理解](https://www.volcengine.com/docs/82379/1902647)

<div data-tips="true" data-tips-type="tip" data-tips-is-title="true">说明</div>


<div data-tips="true" data-tips-type="tip">文档理解详细说明请参见 <a href="https://www.volcengine.com/docs/82379/1902647">文档理解</a>。</div>



**file_data** `string`  |  文件数据

`messages.content.file.file_data`

文件内容的 Base64 编码。单个文件大小要求不超过 50 MB



**file_id** `string`  |  文件 ID

`messages.content.file.file_id`

文件 ID。


* 文件 ID 是通过 [Files API](https://www.volcengine.com/docs/82379/1870405)上传文件后返回的 id。

* **file_id** 对应的文件类型需要和 **type** 保持一致，且文件状态需要为 **active** 。

* **API Key** 所属项目与 **file_id** 上传时所属项目需保持一致


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">Chat API 支持通过 <strong>file_id</strong> 传入火山引擎 TOS Bucket 中的文件，支持该能力的模型范围如下：</div>



* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-mini 系列：doubao\-seed\-2\-0\-mini\-260428 及后续版本。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-lite 系列：全版本支持。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-pro 系列：全版本支持。</div>




**file_url** `string`  |  资源 URL

`messages.content.file.file_url`

文件的可访问 URL。对应文件的大小要求不超过 50 MB



**filename** `string`  |  文件名

`messages.content.file.filename`

文件名。当使用 **file_data** 时该参数必填




**type** `string` `必选`  |  类型

`messages.content.type`

消息模态，此处固定为 `file`






**role** `string` `必选`  |  角色

`messages.role`

发送消息的角色，取值固定为 `system`。



**name** `string`  |  参与者名称

`messages.name`

参与者名称，帮助模型区分不同的参与者




用户消息 `object`

用户消息，用户角色发送的消息。不同模型支持的字段类型不同。


**content** `string / object[]` `必选`  |  消息内容

`messages.content`

用户消息的内容，支持纯文本或多模态内容


纯文本 `string`

纯文本内容



多模态内容 `object[]`

多模态内容，支持文本、图片、视频、音频等模态内容。


文本信息 `object`

文本部分，多模态消息中文本模态的部分。


**text** `string` `必选`  |  文本内容

`messages.content.text`

文本模态部分的内容



**type** `string` `必选`  |  类型

`messages.content.type`

内容模态类型，此处固定为 `text`




图片信息 `object`

图片部分


**image_url** `object` `必选`  |  图片内容

`messages.content.image_url`

图片模态的内容。 图片输入支持 **file_id、url** 两个字段，需二选一传入。具体使用请参见 [图片理解说明](https://www.volcengine.com/docs/82379/1362931)


**url** `string` `必选`  |  资源 URL

`messages.content.image_url.url`

发给模型的图片 URL。支持格式如下：


* 图片链接

* 图片的 Base64 编码



**detail** `string`  |  图片解析粒度

`messages.content.image_url.detail`

图片解析粒度。

理解图片的精细度、不同模型默认取值及对应的具体像素区间，参见 [控制图片理解的精细度](https://www.volcengine.com/docs/82379/1362931#bf4d9224)。可选值：`low`、`high`、`xhigh`。



**file_id** `string`  |  文件 ID

`messages.content.image_url.file_id`

文件 ID。


* 文件 ID 是通过 [Files API](https://www.volcengine.com/docs/82379/1870405)上传文件后返回的 id。

* **file_id** 对应的文件类型需要和 **type** 保持一致，且文件状态需要为 **active** 。

* **API Key** 所属项目与 **file_id** 上传时所属项目需保持一致


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">Chat API 支持通过 <strong>file_id</strong> 传入火山引擎 TOS Bucket 中的文件，支持该能力的模型范围如下：</div>



* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-mini 系列：doubao\-seed\-2\-0\-mini\-260428 及后续版本。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-lite 系列：全版本支持。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-pro 系列：全版本支持。</div>




**image_pixel_limit** `object` `默认值 null`  |  图片像素限制

`messages.content.image_url.image_pixel_limit`

输入给模型的图片的像素范围，如不在此范围，图片会被等比例缩放至该范围。


* 生效优先级：高于 **detail** 字段，即同时配置 **detail** 与 **image_pixel_limit** 字段时，生效 **image_pixel_limit** 字段配置。

* 默认生效规则：若未设置 **image_pixel_limit** ，则使用 **detail** 配置的值对应的 **min_pixels** / **max_pixels** 值。


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">图片像素范围需在 [196, 36,000,000]，否则会直接报错。</div>



**max_pixels** `integer`  |  最大像素

`messages.content.image_url.image_pixel_limit.max_pixels`

传入图片最大像素限制，大于此像素则等比例缩小至 `max_pixels` 字段取值以下。若未设置，则取值为 `detail` 配置的值对应的 `max_pixels` 值。

**模型支持** ：


* **doubao\-seed\-1.8 之前的模型** ：最大值 `4014080`

* **doubao\-seed\-1.8、doubao\-seed\-2.0 模型** ：最大值 `9031680`



**min_pixels** `integer`  |  最小像素

`messages.content.image_url.image_pixel_limit.min_pixels`

传入图片最小像素限制，小于此像素则等比例放大至 `min_pixels` 字段取值以上。若未设置，则取值为 `detail` 配置的值对应的 `min_pixels` 值。

**模型支持** ：


* **doubao\-seed\-1.8 之前的模型** ：最小值 `3136`

* **doubao\-seed\-1.8、doubao\-seed\-2.0 模型** ：最小值 `1764`





**type** `string` `必选`  |  类型

`messages.content.type`

内容模态类型，此处固定为 `image_url`




视频信息 `object`

视频部分


**type** `string` `必选`  |  类型

`messages.content.type`

内容模态类型，此处固定为 `video_url`



**video_url** `object` `必选`  |  视频内容

`messages.content.video_url`

视频消息的内容部分。 视频输入支持 **file_id、url** 两个字段，需二选一传入。具体使用请参见 [视频理解说明](https://www.volcengine.com/docs/82379/1895586)


**url** `string` `必选`  |  资源 URL

`messages.content.video_url.url`

发给模型的视频 URL。支持格式如下：


* 视频链接

* 视频的 Base64 编码



**detail** `string`  |  图片解析粒度

`messages.content.video_url.detail`

从视频中提取帧的精细度



**file_id** `string`  |  文件 ID

`messages.content.video_url.file_id`

文件 ID。


* 文件 ID 是通过 [Files API](https://www.volcengine.com/docs/82379/1870405)上传文件后返回的 id。

* **file_id** 对应的文件类型需要和 **type** 保持一致，且文件状态需要为 **active** 。

* **API Key** 所属项目与 **file_id** 上传时所属项目需保持一致


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">Chat API 支持通过 <strong>file_id</strong> 传入火山引擎 TOS Bucket 中的文件，支持该能力的模型范围如下：</div>



* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-mini 系列：doubao\-seed\-2\-0\-mini\-260428 及后续版本。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-lite 系列：全版本支持。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-pro 系列：全版本支持。</div>




**fps** `number` `默认值 1.0`  |  视频帧率

`messages.content.video_url.fps`

抽帧频率，详见 [视频理解](https://www.volcengine.com/docs/82379/1895586)。


* 取值越高，对视频中画面变化越敏感。

* 取值越低，对视频中画面变化越迟钝，但 token 花费少，速度更快。


**取值范围** ：`[0.2, 5]`



**image_pixel_limit** `object`  |  图片像素限制

`messages.content.video_url.image_pixel_limit`

视频抽帧后应用的像素范围限制


**max_pixels** `integer`  |  最大像素

`messages.content.video_url.image_pixel_limit.max_pixels`

提取帧的最大像素限制



**min_pixels** `integer`  |  最小像素

`messages.content.video_url.image_pixel_limit.min_pixels`

提取帧的最小像素限制






音频信息 `object`

音频部分


**input_audio** `object` `必选`  |  音频内容

`messages.content.input_audio`

音频模态的内容。 音频输入支持 **file_id、url、data** 三个字段，需三选一传入。具体使用请参见 [音频理解](https://www.volcengine.com/docs/82379/2377589)

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>



* <div data-tips="true" data-tips-type="warning">文件大小不超过 25 MB。</div>


* <div data-tips="true" data-tips-type="warning">单次请求音频总时长不超过 120 分钟，仅统计纯音频时长，视频内嵌音频不计入统计。</div>


* <div data-tips="true" data-tips-type="warning">详细说明请参见 <a href="https://www.volcengine.com/docs/82379/2377589">音频理解</a>。</div>




**data** `string`  |  音频数据

`messages.content.input_audio.data`

音频内容的 Base64 编码



**file_id** `string`  |  文件 ID

`messages.content.input_audio.file_id`

文件 ID。


* 文件 ID 是通过 [Files API](https://www.volcengine.com/docs/82379/1870405)上传文件后返回的 id。

* **file_id** 对应的文件类型需要和 **type** 保持一致，且文件状态需要为 **active** 。

* **API Key** 所属项目与 **file_id** 上传时所属项目需保持一致


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">Chat API 支持通过 <strong>file_id</strong> 传入火山引擎 TOS Bucket 中的文件，支持该能力的模型范围如下：</div>



* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-mini 系列：doubao\-seed\-2\-0\-mini\-260428 及后续版本。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-lite 系列：全版本支持。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-pro 系列：全版本支持。</div>




**format** `string`  |  音频格式

`messages.content.input_audio.format`

音频格式。当使用 **data** 时，该参数必填。支持的音频格式 `MIME` 类型如下： 纯音频格式：


* mp3：`audio/mpeg`

* wav：`audio/wav`

* aac：`audio/aac`

* m4a：`audio/m4a`

   视频内嵌音频格式：

* mp3：`audio/mpeg`

* wav：`audio/wav`

* aac：`audio/aac`

* m4a：`audio/m4a`

* pcm：`audio/L16`

* ac3：`audio/ac3`

* alac：`audio/m4a`



**url** `string`  |  资源 URL

`messages.content.input_audio.url`

音频内容的 URL




**type** `string` `必选`  |  类型

`messages.content.type`

内容模态类型，此处固定为 `input_audio`




文件信息 `object`

文件部分


**file** `object` `必选`  |  文件内容

`messages.content.file`

文件模态的内容，当前仅支持 PDF 文件。 文件输入支持 **file_id、file_data、file_url** 三个字段，需三选一传入。多模态理解示例见 [文档理解](https://www.volcengine.com/docs/82379/1902647)

<div data-tips="true" data-tips-type="tip" data-tips-is-title="true">说明</div>


<div data-tips="true" data-tips-type="tip">文档理解详细说明请参见 <a href="https://www.volcengine.com/docs/82379/1902647">文档理解</a>。</div>



**file_data** `string`  |  文件数据

`messages.content.file.file_data`

文件内容的 Base64 编码。单个文件大小要求不超过 50 MB



**file_id** `string`  |  文件 ID

`messages.content.file.file_id`

文件 ID。


* 文件 ID 是通过 [Files API](https://www.volcengine.com/docs/82379/1870405)上传文件后返回的 id。

* **file_id** 对应的文件类型需要和 **type** 保持一致，且文件状态需要为 **active** 。

* **API Key** 所属项目与 **file_id** 上传时所属项目需保持一致


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">Chat API 支持通过 <strong>file_id</strong> 传入火山引擎 TOS Bucket 中的文件，支持该能力的模型范围如下：</div>



* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-mini 系列：doubao\-seed\-2\-0\-mini\-260428 及后续版本。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-lite 系列：全版本支持。</div>


* <div data-tips="true" data-tips-type="warning">doubao\-seed\-2.0\-pro 系列：全版本支持。</div>




**file_url** `string`  |  资源 URL

`messages.content.file.file_url`

文件的可访问 URL。对应文件的大小要求不超过 50 MB



**filename** `string`  |  文件名

`messages.content.file.filename`

文件名。当使用 **file_data** 时该参数必填




**type** `string` `必选`  |  类型

`messages.content.type`

消息模态，此处固定为 `file`






**role** `string` `必选`  |  角色

`messages.role`

发送消息的角色，取值固定为 `user`。



**name** `string`  |  参与者名称

`messages.name`

参与者名称，帮助模型区分不同的参与者




模型消息 `object`

模型消息，历史对话中模型角色返回的消息。用以保持对话一致性，多在 [多轮对话](https://www.volcengine.com/docs/82379/1399009#f6222fec)及 [续写模式](https://www.volcengine.com/docs/82379/1359497)使用。


**role** `string` `必选`  |  角色

`messages.role`

发送消息的角色，取值固定为 `assistant`。



**content** `string`  |  消息内容

`messages.content`

模型消息的内容。

<div data-tips="true" data-tips-type="tip" data-tips-is-title="true">说明</div>


<div data-tips="true" data-tips-type="tip"><code>messages.content</code> 与 <code>messages.tool_calls</code> 至少填写其一。</div>




**encrypted_content** `string`  |  加密思考内容

`messages.encrypted_content`

经加密及压缩处理后的思考内容原文。自 `doubao-seed-2-0-lite-260428` 版本起，支持该字段输出。

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>



* <div data-tips="true" data-tips-type="warning">回传 <code>encrypted_content</code> 内容需有效，篡改或无法还原时返回错误：<code>Invalid signature</code>。</div>


* <div data-tips="true" data-tips-type="warning"><code>encrypted_content</code> 优先级高于 <code>reasoning_content</code>，回传 <code>encrypted_content</code> 时，将忽略 <code>reasoning_content</code> 内容。</div>




**name** `string`  |  参与者名称

`messages.name`

参与者名称，帮助模型区分不同的参与者



**reasoning_content** `string`  |  思维链内容

`messages.reasoning_content`

模型消息中思维链内容。

**模型支持** ：


* `doubao-seed-1.8`

* `deepseek-v3.2`

* `doubao-seed-2.0`

* `doubao-seed-2.1`



**tool_calls** `object[]`  |  工具调用

`messages.tool_calls`

模型消息中工具调用部分


**function** `object` `必选`  |  函数信息

`messages.tool_calls.function`

模型调用的函数


**arguments** `string` `必选`  |  函数参数

`messages.tool_calls.function.arguments`

模型生成的用于调用函数的参数，JSON 格式。 模型并不总是生成有效的 JSON，并且可能会虚构出一些您的函数参数规范中未定义的参数。在调用函数之前，请在您的代码中验证这些参数是否有效



**name** `string` `必选`  |  函数名

`messages.tool_calls.function.name`

模型调用的函数名称




**id** `string` `必选`  |  ID

`messages.tool_calls.id`

调用的工具的 ID



**type** `string` `必选`  |  类型

`messages.tool_calls.type`

工具类型，当前仅支持`function`





工具消息 `object`

工具消息，历史对话中调用工具返回的消息。工具调用场景中使用。


**content** `string` `必选`  |  消息内容

`messages.content`

工具返回的消息。



**role** `string` `必选`  |  角色

`messages.role`

发送消息的角色，取值固定为 `tool`。



**tool_call_id** `string` `必选`  |  工具调用 ID

`messages.tool_call_id`

模型生成的需调用工具请求时，生成的 ID。在程序调用工具的返回需要附上同一 ID，来关联工具结构与模型请求。避免多工具调用时混淆信息



**name** `string`  |  参与者名称

`messages.name`

参与者名称，帮助模型区分不同的参与者





**model** `string` `必选`  |  模型 ID

调用的模型 ID（Model ID）。[开通模型服务](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement?LLM=%7B%7D&OpenTokenDrawer=false) 后可 [查询 Model ID](https://www.volcengine.com/docs/82379/1330310)。

多个应用及精细管理场景，推荐使用 Endpoint ID 调用，详细请参考 [获取 Endpoint ID](https://www.volcengine.com/docs/82379/1099522)。



**frequency_penalty** `number` `默认值 0.0`  |  频率惩罚系数

如值为正，根据新 token 在文本中的出现频率对其进行惩罚，从而降低模型逐字重复的可能性。

**取值范围** ：`[-2.0, 2.0]`

**不支持模型** ：


* `doubao-seed-1.8 系列`

* `doubao-seed-2.0 系列`



**logit_bias** `object` `默认值 null`  |  Token 偏差

调整指定 token 在模型输出内容中出现的概率，使模型生成的内容更加符合特定的偏好。

`logit_bias` 接受一个 map。每个键为词表中的 token ID（可通过 tokenization 接口获取），每个值为该 token 的偏差值：


* 负值降低选择该 token 的可能性；`-100` 会完全禁止选择该 token。

* 正值增加选择该 token 的可能性；`100` 会导致仅可选择该 token。


示例：`{"<Token_ID>": -100}`。该参数的实际效果可能因模型而异。

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">带深度思考能力模型不支持该字段，深度思考能力模型参见 <a href="https://www.volcengine.com/docs/82379/1330310#43b6e6a1">文档</a>。</div>


**取值范围** ：`[-100, 100]`



**logprobs** `boolean` `默认值 false`  |  返回对数概率

是否返回输出 tokens 的对数概率。


* `false`：不返回对数概率信息。

* `true`：返回消息内容中每个输出 token 的对数概率。


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">带深度思考能力模型不支持该字段，深度思考能力模型参见 <a href="https://www.volcengine.com/docs/82379/1330310#43b6e6a1">文档</a>。</div>




**max_completion_tokens** `integer`  |  最大输出长度

控制模型输出的最大长度（包括模型回答和模型思维链内容长度，单位 token）。

配置了该参数后，可以让模型输出超长内容，`max_tokens` 默认值失效，模型按需输出内容（回答和思维链），直到达到 `max_completion_tokens` 值。

不可与 `max_tokens` 字段同时设置。

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">支持该字段的模型及使用说明见 <a href="https://www.volcengine.com/docs/82379/1449737">文档</a>。</div>


**取值范围** ：`[1, 65536]`



**max_tokens** `integer` `默认值 4096`  |  最大回答长度

模型回答最大长度（单位 token）。取值范围各个模型不同，详细见 [模型列表](https://www.volcengine.com/docs/82379/1330310)。

<div data-tips="true" data-tips-type="tip" data-tips-is-title="true">说明</div>



* <div data-tips="true" data-tips-type="tip">模型回答不包含思维链内容，模型回答 = 模型输出 \- 模型思维链（如有）</div>


* <div data-tips="true" data-tips-type="tip">输出 token 的总长度还受模型的上下文长度限制。</div>




**parallel_tool_calls** `boolean` `默认值 true`  |  并行工具调用

本次请求，模型返回是否允许包含多个待调用的工具。


* `true`：允许返回多个待调用的工具。

* `false`：允许返回的待调用的工具小于等于 1。


**模型支持** ：


* **doubao\-seed\-1.6** ：及之后系列模型；仅当 parallel_tool_calls=false 时该值受模型支持限制，true 全模型通用



**presence_penalty** `number` `默认值 0.0`  |  存在惩罚系数

如果值为正，会根据新 token 到目前为止是否出现在文本中对其进行惩罚，从而增加模型谈论新主题的可能性。

**取值范围** ：`[-2.0, 2.0]`

**不支持模型** ：


* `doubao-seed-1.8 系列`

* `doubao-seed-2.0 系列`



**reasoning_effort** `string` `默认值 medium`  |  思考深度

限制思考的工作量。减少思考深度可提升速度，思考花费的 token 更少。


* `none`：不开启思考（仅 `glm-5-2-260617` 支持）。

* `minimal`：关闭思考，直接回答。

* `low`：轻量思考，侧重快速响应。

* `medium`：均衡模式，兼顾速度与深度。

* `high`：深度分析，处理复杂问题。

* `xhigh`：更深层次的推理（仅 `glm-5-2-260617` 支持）。

* `max`：最高程度思考，适配高难度推理任务。


<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>



* <div data-tips="true" data-tips-type="warning">支持该字段的模型、与 <code>thinking.type</code> 字段关系见 <a href="https://www.volcengine.com/docs/82379/1449737">文档</a>。</div>


* <div data-tips="true" data-tips-type="warning"><code>max</code> 取值仅 <code>glm-5-2-260617</code>、<code>deepseek-v4-pro-260425</code>、<code>deepseek-v4-flash-260425</code> 支持。</div>


* <div data-tips="true" data-tips-type="warning"><code>none</code>、<code>xhigh</code> 取值仅 <code>glm-5-2-260617</code> 支持。</div>




**response_format** `object`  |  回答格式

指定模型回答格式。默认值：`{"type": "text"}`

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>



* <div data-tips="true" data-tips-type="warning">支持该字段的模型请参见 <a href="https://www.volcengine.com/docs/82379/1568221#3aae5325">文档</a>。</div>


* <div data-tips="true" data-tips-type="warning">该能力尚在 beta 阶段，请谨慎在生产环境使用。</div>




**json_schema** `object`  |  Schema 配置

`response_format.json_schema`

JSON 结构体的定义


**name** `string` `必选`  |  Schema 名称

`response_format.json_schema.name`

JSON Schema 的名称，用于标识本次响应格式



**schema** `object` `必选`  |  Schema 定义

`response_format.json_schema.schema`

回答格式的 JSON Schema 定义



**description** `string`  |  描述

`response_format.json_schema.description`

回答用途说明，模型据此判断如何按该格式生成回答



**strict** `boolean` `默认值 false`  |  严格模式

`response_format.json_schema.strict`

是否在生成输出时，启用严格遵循模式。


* `true`：模型将始终严格遵循 `schema` 字段中定义的格式。

* `false`：模型会尽可能遵循 `schema` 字段中定义的结构。




**type** `string`  |  类型

`response_format.type`

回答格式类型




**service_tier** `string` `默认值 auto`  |  推理模式

控制使用的在线推理模式。


* `fast`：本次请求优先使用 [在线推理（低延迟）](https://www.volcengine.com/docs/82379/2335857) 模式。

   * 推理接入点（`model` 字段指定）有低延迟限流配额，本次请求将会优先使用低延迟限流配额，获得更高的服务等级（延迟、可用性等）。

   * 推理接入点无低延迟限流配额，或者限流配额已满，降级至 **在线推理（常规）**  模式，维持常规的服务等级。

* `auto`：本次请求优先使用 [在线推理（TPM 保障包）](https://www.volcengine.com/docs/82379/1510762) 模式。

   * 推理接入点有 TPM 保障包额度，本次请求将会优先使用 TPM 保障包额度，获得最高的服务等级。

   * 推理接入点无 TPM 保障包额度或用超额度，降级至 **在线推理（常规）**  模式，维持常规的服务等级。

* `default`：本次请求只使用 [在线推理（常规）](https://www.volcengine.com/docs/82379/2121998) 模式。维持常规的服务等级，即使调用的推理接入点有 TPM 保障包额度 / 低延迟限流额度。



**stop** `string / string[]` `默认值 null`  |  停止词

模型遇到 `stop` 字段所指定的字符串时将停止继续生成，这个词语本身不会输出。最多支持 4 个字符串。

示例：`["你好", "天气"]`。

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning"><a href="https://www.volcengine.com/docs/82379/1330310">深度思考能力模型</a>不支持该字段。</div>




**stream** `boolean` `默认值 false`  |  流式返回

响应内容是否流式返回。


* `false`：模型生成完所有内容后一次性返回结果。

* `true`：按 SSE 协议逐块返回模型生成内容，并以一条 `data: [DONE]` 消息结束。当 `stream` 为 `true` 时，可设置 `stream_options` 字段以获取 token 用量统计信息。



**stream_options** `object` `默认值 null`  |  流式选项

流式响应的选项。当 `stream` 为 `true` 时，可设置本字段。


**chunk_include_usage** `boolean` `默认值 false`  |  逐块用量信息

`stream_options.chunk_include_usage`

模型流式输出时，输出的每个 chunk 中是否输出本次请求到此 chunk 输出时刻的累计 token 用量信息。


* `true`：在返回的 `usage` 字段中，输出本次请求到此 chunk 输出时刻的累计 token 用量。

* `false`：不在每个 chunk 都返回 token 用量信息。



**include_usage** `boolean` `默认值 false`  |  输出用量信息

`stream_options.include_usage`

模型流式输出时，是否在输出结束前输出本次请求的 token 用量信息。


* `true`：在 `data: [DONE]` 消息之前会返回一个额外的 chunk。此 chunk 中，`usage` 字段中输出整个请求的 token 用量，`choices` 字段为空数组。

* `false`：输出结束前，没有一个 chunk 来返回 token 用量信息。




**temperature** `number` `默认值 1.0`  |  采样温度

控制了生成文本时对每个候选词的概率分布进行平滑的程度。当取值为 0 时模型仅考虑对数概率最大的一个 token。

较高的值（如 0.8）会使输出更加随机，而较低的值（如 0.2）会使输出更加集中确定。

通常建议仅调整 `temperature` 或 `top_p` 其中之一，不建议两者都修改。

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">调用下列模型时字段取值固定为 <code>1</code>，手动指定的参数值将被忽略：</div>



* <div data-tips="true" data-tips-type="warning"><code>doubao-seed-2-0-pro-260215</code></div>


* <div data-tips="true" data-tips-type="warning"><code>doubao-seed-2-0-lite-260215</code></div>



**取值范围** ：`[0, 2]`



**thinking** `object`  |  深度思考开关

控制模型是否开启深度思考模式。

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">不同模型是否支持以及默认取值不同，详情请查询 <a href="https://www.volcengine.com/docs/82379/1449737#14b5c6db">文档</a>。</div>



**type** `string`  |  类型

`thinking.type`

控制模型是否开启思考模式。


* `enabled`：开启思考模式，模型强制先思考再回答。

* `disabled`：关闭思考模式，模型直接回答问题，不进行思考。

* `auto`：自动思考模式，模型根据问题自主判断是否需要思考，简单题目直接回答。




**tool_choice** `string / object`  |  工具调用控制

本次请求，模型返回信息中是否有待调用的工具。


* `none`：模型不会调用工具，直接生成消息。当没有指定工具时，`none` 是默认值。

* `auto`：模型可以选择生成消息或调用工具。如果存在工具，则 `auto` 是默认值。

* `required`：模型必须调用一个或多个工具。


您也可以通过设置 `tool_choice` 为 object 类型，来强制模型调用指定工具。

**模型支持** ：


* `doubao-seed-1.6 及之后系列`



枚举值 `string`

控制模型返回是否包含待调用的工具。


* `none`：模型返回信息中不可含有待调用的工具。

* `required`：模型返回信息中必须含待调用的工具。选择此项时请确认存在适合的工具，以减少模型产生幻觉的情况。

* `auto`：模型自行判断返回信息是否有待调用的工具。



指定工具 `object`

指定待调用工具的范围。模型返回信息中，只允许包含以下模型信息。

选择此项时请确认该工具适合用户需求，以减少模型产生幻觉的情况。


**function** `object` `必选`  |  函数信息

`tool_choice.function`

调用工具的信息


**name** `string` `必选`  |  函数名

`tool_choice.function.name`

要调用的函数名称




**type** `string` `必选`  |  类型

`tool_choice.type`

调用的类型，此处应为 `function`





**tools** `object[]` `默认值 null`  |  工具列表

待调用工具的列表，模型返回信息中可包含。

当您需要让模型返回待调用工具时，需要配置该结构体。支持该字段的模型请参见 [文档](https://www.volcengine.com/docs/82379/1330310#f44ceef7)。


**function** `object` `必选`  |  函数信息

`tools.function`

模型返回中可包含待调用的工具


**name** `string` `必选`  |  函数名

`tools.function.name`

工具（函数）名称，供模型识别与调用



**description** `string`  |  描述

`tools.function.description`

调用的函数的描述，大模型会使用它来判断是否调用这个工具



**parameters** `object`  |  参数定义

`tools.function.parameters`

函数请求参数，以 JSON Schema 格式描述。具体格式请参考 [JSON Schema](https://json-schema.org/understanding-json-schema) 文档。

格式如下：

```JSON
{ "type": "object", "properties": { "参数名": { "type": "string | number | boolean | object | array", "description": "参数说明" } }, "required": ["必填参数"] }
```


使用要点：所有字段名大小写敏感；`parameters` 须是合规的 JSON Schema 对象；建议用英文字段名，中文置于 `description` 字段中。




**type** `string` `必选`  |  类型

`tools.type`

工具类型，此处应为 `function`




**top_logprobs** `integer` `默认值 0`  |  返回概率数量

指定每个输出 token 位置最有可能返回的 token 数量，每个 token 都有关联的对数概率。仅当 `logprobs` 为 `true` 时可以设置本参数。

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">带深度思考能力模型不支持该字段，深度思考能力模型参见 <a href="https://www.volcengine.com/docs/82379/1330310#43b6e6a1">文档</a>。</div>


**取值范围** ：`[0, 20]`



**top_p** `number` `默认值 0.7`  |  核采样阈值

核采样概率阈值。模型会考虑概率质量在 `top_p` 内的 token 结果。

当取值为 0 时模型仅考虑对数概率最大的一个 token。0.1 意味着只考虑概率质量最高的前 10% 的 token，取值越大生成的随机性越高，取值越低生成的确定性越高。

通常建议仅调整 `temperature` 或 `top_p` 其中之一，不建议两者都修改。

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">调用下列模型时字段取值固定为 <code>0.95</code>，手动指定的参数值将被忽略：</div>



* <div data-tips="true" data-tips-type="warning"><code>doubao-seed-2-0-pro-260215</code></div>


* <div data-tips="true" data-tips-type="warning"><code>doubao-seed-2-0-lite-260215</code></div>


* <div data-tips="true" data-tips-type="warning"><code>doubao-seed-1-8-251228</code></div>



**取值范围** ：`[0, 1]`


&nbsp;

<span id=".5ZON5bqU5Y-C5pWw"></span>
## 响应参数

<span id=".6Z2e5rWB5byP6LCD55So5ZON5bqU"></span>
### 非流式调用响应


**choices** `object[]`  |  生成结果

本次请求的模型输出内容


**finish_reason** `string`  |  结束原因

`choices.finish_reason`

模型停止生成 token 的原因。


* `stop`：模型输出自然结束，或因命中请求参数 `stop` 中指定的字段而被截断。

* `length`：模型输出因达到模型输出限制而被截断，有以下原因：

   * 触发 `max_tokens` 限制（回答内容的长度限制）。

   * 触发 `max_completion_tokens` 限制（思维链内容 + 回答内容的长度限制）。

   * 触发 `context_window` 限制（输入内容 + 思维链内容 + 回答内容的长度限制）。

* `content_filter`：模型输出被内容审核拦截。

* `tool_calls`：模型调用了工具。



**index** `integer`  |  序号

`choices.index`

当前元素在 **choices** 列表的索引



**logprobs** `object`  |  选项对数概率详情

`choices.logprobs`

当前内容的对数概率信息


**content** `object[]`  |  消息内容

`choices.logprobs.content`

message 列表中每个 content 元素中的 token 对数概率信息


**bytes** `integer[]`  |  字节

`choices.logprobs.content.bytes`

当前 token 的 UTF\-8 值，格式为整数列表。当一个字符由多个 token 组成（表情符号或特殊字符等）时可以用于字符的编码和解码。如果 token 没有 UTF\-8 值则为空



**logprob** `number`  |  对数概率值

`choices.logprobs.content.logprob`

当前 token 的对数概率



**token** `string`  |  Token

`choices.logprobs.content.token`

当前 token



**top_logprobs** `object[]`  |  候选概率

`choices.logprobs.content.top_logprobs`

在当前 token 位置最有可能的标记及其对数概率的列表。在一些情况下，返回的数量可能比请求参数 top_logprobs 指定的数量要少


**bytes** `integer[]`  |  字节

`choices.logprobs.content.top_logprobs.bytes`

当前 token 的 UTF\-8 值，格式为整数列表。当一个字符由多个 token 组成（表情符号或特殊字符等）时可以用于字符的编码和解码。如果 token 没有 UTF\-8 值则为空



**logprob** `number`  |  对数概率值

`choices.logprobs.content.top_logprobs.logprob`

当前 token 的对数概率



**token** `string`  |  Token

`choices.logprobs.content.top_logprobs.token`

当前 token






**message** `object`  |  消息

`choices.message`

模型输出的内容


**content** `string`  |  消息内容

`choices.message.content`

模型生成的消息内容



**role** `string`  |  角色

`choices.message.role`

内容输出的角色，此处固定为 `assistant`



**reasoning_content** `string`  |  思维链内容

`choices.message.reasoning_content`

模型处理问题的思维链内容。

**模型支持** ：


* `doubao-seed-1.8`

* `deepseek-v3.2`

* `doubao-seed-2.0`

* `doubao-seed-2.1`



**tool_calls** `object[]`  |  工具调用

`choices.message.tool_calls`

模型生成的工具调用


**function** `object`  |  函数信息

`choices.message.tool_calls.function`

模型调用的函数


**arguments** `string`  |  函数参数

`choices.message.tool_calls.function.arguments`

模型生成的用于调用函数的参数，JSON 格式。 模型并不总是生成有效的 JSON，并且可能会虚构出一些您的函数参数规范中未定义的参数。在调用函数之前，请在您的代码中验证这些参数是否有效



**name** `string`  |  函数名

`choices.message.tool_calls.function.name`

模型调用的函数名称




**id** `string`  |  ID

`choices.message.tool_calls.id`

调用的工具的 ID



**type** `string`  |  类型

`choices.message.tool_calls.type`

工具类型，当前仅支持`function`





**moderation_hit_type** `string`  |  审核命中类型

`choices.moderation_hit_type`

模型输出文字含有敏感信息时，会返回模型输出文字命中的风险分类标签。


* `severe_violation`：模型输出文字涉及严重违规。

* `violence`：模型输出文字涉及激进行为。


<div data-tips="true" data-tips-type="tip" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="tip">注意：当前只有 <a href="https://www.volcengine.com/docs/82379/1362931#f8d6cc48">视觉理解模型</a>支持返回该字段，且只有在方舟控制台 <a href="https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint/create?customModelId=">接入点配置页面</a> 或者 <a href="https://www.volcengine.com/api-reference/control-plane/endpoints/createendpoint.md">CreateEndpoint</a> 接口中，将内容护栏方案（ModerationStrategy）设置为基础方案（Basic）时，才会返回风险分类标签。</div>





**created** `integer`  |  创建时间

本次请求创建时间的 Unix 时间戳（秒）



**id** `string`  |  请求 ID

本次请求的唯一标识



**model** `string`  |  模型名称

本次请求实际使用的模型名称和版本



**object** `string`  |  对象类型

固定为 `chat.completion`



**service_status** `object`  |  服务状态

本次请求附带的服务状态信息，例如是否触发了模型降级（fallback）


**model_fallback** `object`  |  模型降级状态

`service_status.model_fallback`

模型降级（fallback）相关的状态信息


**fallback_triggered** `boolean`  |  是否触发降级

`service_status.model_fallback.fallback_triggered`

本次请求是否触发了模型降级



**original_model** `string`  |  原始模型

`service_status.model_fallback.original_model`

触发降级前，请求最初指定的模型名称





**service_tier** `string`  |  推理模式

本次请求实际使用的推理模式。


* `scale`：本次请求使用 [在线推理（TPM 保障包）](https://www.volcengine.com/docs/82379/1510762) 模式。

* `default`：本次请求使用 [在线推理（常规）](https://www.volcengine.com/docs/82379/2121998) 模式。

* `fast`：本次请求使用 [在线推理（低延迟）](https://www.volcengine.com/docs/82379/2335857) 模式。



**usage** `object`  |  Token 用量

本次请求的 token 用量


**completion_tokens** `integer`  |  输出 Token 数

`usage.completion_tokens`

模型输出内容花费的 token



**completion_tokens_details** `object`  |  输出 Token 明细

`usage.completion_tokens_details`

模型输出内容花费的 token 的细节


**reasoning_tokens** `integer`  |  思维链 Token 数

`usage.completion_tokens_details.reasoning_tokens`

输出思维链内容花费的 token 数。 支持输出思维链的模型请参见 [文档](https://www.volcengine.com/docs/82379/1449737#14b5c6db)




**prompt_tokens** `integer`  |  输入 Token 数

`usage.prompt_tokens`

输入给模型处理的内容 token 数量



**prompt_tokens_details** `object`  |  输入 Token 明细

`usage.prompt_tokens_details`

输入给模型处理的内容 token 数量的细节


**cached_tokens** `integer`  |  缓存命中 Token 数

`usage.prompt_tokens_details.cached_tokens`

缓存命中的输入内容（含文本、音频等所有类型）所消耗的 token 总数



**audio_cached_tokens** `integer`  |  音频缓存 Token 数

`usage.prompt_tokens_details.audio_cached_tokens`

缓存命中的音频输入内容所消耗的 token 数量



**audio_tokens** `integer`  |  音频 Token 数

`usage.prompt_tokens_details.audio_tokens`

音频输入内容所消耗的 token 数量




**total_tokens** `integer`  |  总 Token 数

`usage.total_tokens`

本次请求消耗的总 token 数量（输入 + 输出）



&nbsp;

<span id=".5rWB5byP6LCD55So5ZON5bqU"></span>
### 流式调用响应


**choices** `object[]`  |  生成结果

本次请求的模型输出内容


**delta** `object`  |  增量消息

`choices.delta`

模型输出的增量内容


**content** `string`  |  消息内容

`choices.delta.content`

模型生成的消息内容



**encrypted_content** `string`  |  加密思考内容

`choices.delta.encrypted_content`

经加密及压缩处理后的思考内容原文。自 `doubao-seed-2-0-lite-260428` 版本起，支持该字段输出。

<div data-tips="true" data-tips-type="tip" data-tips-is-title="true">说明</div>


<div data-tips="true" data-tips-type="tip">流式输出场景下，将在思考内容输出完成后、正式应答内容输出前，输出包含完整 <code>encrypted_content</code> 的数据。其中 <code>content</code> 与 <code>reasoning_content</code> 字段均为空。</div>




**reasoning_content** `string`  |  思维链内容

`choices.delta.reasoning_content`

思考内容原文。

自 `doubao-seed-2-0-lite-260428` 版本起，返回思考内容摘要。

<div data-tips="true" data-tips-type="warning" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="warning">针对长文本生成、深度推理等耗时场景，建议适当调大首 Token 超时时间（TTFT）与逐 Token 生成超时时间（TPOT），避免请求因超时而中断。</div>


**模型支持** ：


* `doubao-seed-1.8`

* `deepseek-v3.2`

* `doubao-seed-2.0`

* `doubao-seed-2.1`



**role** `string`  |  角色

`choices.delta.role`

内容输出的角色，此处固定为 `assistant`



**tool_calls** `object[]`  |  工具调用

`choices.delta.tool_calls`

模型生成的工具调用


**index** `integer`  |  序号

`choices.delta.tool_calls.index`

工具调用在数组中的索引位置



**function** `object`  |  函数信息

`choices.delta.tool_calls.function`

模型调用的函数


**arguments** `string`  |  函数参数

`choices.delta.tool_calls.function.arguments`

模型生成的用于调用函数的参数，JSON 格式。 模型并不总是生成有效的 JSON，并且可能会虚构出一些您的函数参数规范中未定义的参数。在调用函数之前，请在您的代码中验证这些参数是否有效



**name** `string`  |  函数名

`choices.delta.tool_calls.function.name`

模型调用的函数名称




**id** `string`  |  ID

`choices.delta.tool_calls.id`

调用的工具的 ID



**type** `string`  |  类型

`choices.delta.tool_calls.type`

工具类型，当前仅支持`function`





**index** `integer`  |  序号

`choices.index`

当前元素在 **choices** 列表的索引



**finish_reason** `string`  |  结束原因

`choices.finish_reason`

模型停止生成 token 的原因。


* `stop`：模型输出自然结束，或因命中请求参数 `stop` 中指定的字段而被截断。

* `length`：模型输出因达到模型输出限制而被截断，有以下原因：

   * 触发 `max_tokens` 限制（回答内容的长度限制）。

   * 触发 `max_completion_tokens` 限制（思维链内容 + 回答内容的长度限制）。

   * 触发 `context_window` 限制（输入内容 + 思维链内容 + 回答内容的长度限制）。

* `content_filter`：模型输出被内容审核拦截。

* `tool_calls`：模型调用了工具。



**logprobs** `object`  |  选项对数概率详情

`choices.logprobs`

当前内容的对数概率信息


**content** `object[]`  |  消息内容

`choices.logprobs.content`

message 列表中每个 content 元素中的 token 对数概率信息


**bytes** `integer[]`  |  字节

`choices.logprobs.content.bytes`

当前 token 的 UTF\-8 值，格式为整数列表。当一个字符由多个 token 组成（表情符号或特殊字符等）时可以用于字符的编码和解码。如果 token 没有 UTF\-8 值则为空



**logprob** `number`  |  对数概率值

`choices.logprobs.content.logprob`

当前 token 的对数概率



**token** `string`  |  Token

`choices.logprobs.content.token`

当前 token



**top_logprobs** `object[]`  |  候选概率

`choices.logprobs.content.top_logprobs`

在当前 token 位置最有可能的标记及其对数概率的列表。在一些情况下，返回的数量可能比请求参数 top_logprobs 指定的数量要少


**bytes** `integer[]`  |  字节

`choices.logprobs.content.top_logprobs.bytes`

当前 token 的 UTF\-8 值，格式为整数列表。当一个字符由多个 token 组成（表情符号或特殊字符等）时可以用于字符的编码和解码。如果 token 没有 UTF\-8 值则为空



**logprob** `number`  |  对数概率值

`choices.logprobs.content.top_logprobs.logprob`

当前 token 的对数概率



**token** `string`  |  Token

`choices.logprobs.content.top_logprobs.token`

当前 token






**moderation_hit_type** `string`  |  审核命中类型

`choices.moderation_hit_type`

模型输出文字含有敏感信息时，会返回模型输出文字命中的风险分类标签。


* `severe_violation`：模型输出文字涉及严重违规。

* `violence`：模型输出文字涉及激进行为。


<div data-tips="true" data-tips-type="tip" data-tips-is-title="true">注意</div>


<div data-tips="true" data-tips-type="tip">注意：当前只有 <a href="https://www.volcengine.com/docs/82379/1362931#f8d6cc48">视觉理解模型</a>支持返回该字段，且只有在方舟控制台 <a href="https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint/create?customModelId=">接入点配置页面</a> 或者 <a href="https://www.volcengine.com/api-reference/control-plane/endpoints/createendpoint.md">CreateEndpoint</a> 接口中，将内容护栏方案（ModerationStrategy）设置为基础方案（Basic）时，才会返回风险分类标签。</div>





**created** `integer`  |  创建时间

本次请求创建时间的 Unix 时间戳（秒）



**id** `string`  |  请求 ID

本次请求的唯一标识



**model** `string`  |  模型名称

本次请求实际使用的模型名称和版本



**object** `string`  |  对象类型

固定为 `chat.completion.chunk`



**service_status** `object`  |  服务状态

本次请求附带的服务状态信息，例如是否触发了模型降级（fallback）


**model_fallback** `object`  |  模型降级状态

`service_status.model_fallback`

模型降级（fallback）相关的状态信息


**fallback_triggered** `boolean`  |  是否触发降级

`service_status.model_fallback.fallback_triggered`

本次请求是否触发了模型降级



**original_model** `string`  |  原始模型

`service_status.model_fallback.original_model`

触发降级前，请求最初指定的模型名称





**service_tier** `string`  |  推理模式

本次请求实际使用的推理模式。


* `scale`：本次请求使用 [在线推理（TPM 保障包）](https://www.volcengine.com/docs/82379/1510762) 模式。

* `default`：本次请求使用 [在线推理（常规）](https://www.volcengine.com/docs/82379/2121998) 模式。

* `fast`：本次请求使用 [在线推理（低延迟）](https://www.volcengine.com/docs/82379/2335857) 模式。



**usage** `object`  |  Token 用量

本次请求的 token 用量。

流式调用时，默认不统计 token 用量信息，返回值为 `null`。如需统计，需设置 `stream_options.include_usage` 为 `true`。




