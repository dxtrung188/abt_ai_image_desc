# Image Translation Pro Version API Synchronous Interface

**lation Pro Version API Synchronous Interface**

<mark style="color:green;">`GET/POST`</mark> `/ai/image/translation_mllm`

<details>

<summary>Product description</summary>

The Image Translation Pro product is specifically designed for e-commerce images, integrating multimodal large model technology to achieve a more accurate understanding of images. It significantly improves translation quality and continues to expand and optimize multilingual translation capabilities.

</details>

### **Request Parameter** <a href="#request-parameter" id="request-parameter"></a>

| Parameter   | Parameter                      | Type    | Required | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ----------- | ------------------------------ | ------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `paramJson` | `imageUrl`                     | String  | Yes      | <p>Image requirements：No more than 4000x4000 pixel. Size up to 10MB. Supporting png, jpeg, jpgm, bmp, webp.</p><p><code>Sample:</code> <a href="http://example.jpg/"><code>http://example.jpg/</code></a></p>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|             | `sourceLanguage`               | String  | Yes      | <p>Source language code. Supporting languages as the appendix shows.</p><p><code>Sample: en</code></p>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|             | `targetLanguage`               | String  | Yes      | <p>Target language code. Supporting languages as the appendix shows.</p><p><code>Sample: ko</code></p>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
|             | `includingProductArea`         | Boolean | No       | <p>Choose whether to translate the text within the main subject of images; this allows you to preserve and avoid translating embedded information such as product names.</p><p>As shown in the example image, the text in the red box represents the text on the main subject, while the text in the blue box represents text not on the main subject.</p><p><code>Sample: false</code><img src="https://3421660005-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FcXGtrD26wbOKouIXD83g%2Fuploads%2Fi6LaUUAkt4Ujvk6jVUL6%2Fimage.png?alt=media&#x26;token=454d468b-bf86-42bf-83bc-73fe6a53a856" alt=""></p>                                                                                                                                                                                      |
|             | `useImageEditor`               | Boolean | No       | <p>Whether it return layout information such as the position, font, and color of the text. This is used to obtain data for secondary editing when integrating with the image editor.</p><p><code>Sample: false</code></p>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|             | `translatingBrandInTheProduct` | Boolean | No       | <p>Choose whether to translate brand names on the image. This can help you preserve brand name information and prevent it from being translated.</p><p>Default：false（This means not translating the brand name.）</p><p>As shown in the example image，“懒角落”refers to a brand name</p><p><code>Sample："false"</code><img src="https://3421660005-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FcXGtrD26wbOKouIXD83g%2Fuploads%2FFCHSGTMWka6WCVHEEZ1Y%2Fimage.png?alt=media&#x26;token=6dc3d909-c3d5-4830-b014-2dabbcef8cdb" alt="" data-size="original"><img src="https://3421660005-files.gitbook.io/~/files/v0/b/gitbook-x-prod.appspot.com/o/spaces%2FcXGtrD26wbOKouIXD83g%2Fuploads%2Ffot6T2aP7VBruzjM9eTo%2Fimage.png?alt=media&#x26;token=b5456515-f3f0-4a13-aba1-c0e84b3faead" alt=""></p> |

### Sample Request <a href="#npldf" id="npldf"></a>

* For other programming languages, please refer to [Quick Start](https://docs.aidc-ai.com/aidge-resource/getting-started/quick-start).

```
IopClient client = new IopClientImpl(url, appkey, appSecret);
        IopRequest request = new IopRequest();
        request.setApiName("/ai/image/translation_mllm");
// If you have not purchased a formal quota, please add a trial flag; otherwise, you will receive a NoResource error code.
// request.addHeaderParameter("x-iop-trial","true");
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("imageUrl", "https://img.alicdn.com/imgextra/i1/1955749012/O1CN016P3Jas2GRY7vaevsK_!!1955749012.jpg");
        jsonObject.put("sourceLanguage", "zh");
        jsonObject.put("targetLanguage", "en");
        jsonObject.put("translatingBrandInTheProduct", "false");
        jsonObject.put("useImageEditor", "false");
        request.addApiParameter("paramJson", jsonObject.toString());
        IopResponse response = client.execute(request);
        System.out.println(response.getBody());
        Thread.sleep(10);
```

### Parameters Response  <a href="#punx6" id="punx6"></a>

| Parameter    | Type   | Description                                                                                                                  |
| ------------ | ------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `resCode`    | Number | Response code;200 indicates a successful call. For other response codes,please refer to the error code information.          |
| `resMessage` | String | Error message,e.g. "content has sensitive data, please try other input".                                                     |
| `data`       | Object | The final result, where result\_list is the url of the translation result, and edit\_info is the recognized text information |

### **Sample Response** <a href="#sample-response" id="sample-response"></a>

```
{
  "data": {
    "usage": 1,
    "imageResultList": [
        {
            "src_image": "https://img.alicdn.com/imgextra/i1/1955749012/O1CN016P3Jas2GRY7vaevsK_!!1955749012.jpg",
            "result_list": [
                {
                    "fileUrl": "https://aib-image.oss-ap-southeast-1.aliyuncs.com/tufan%2Fd79bca66-4d80-11f0-a4f8-00163e0eb98a.jpg?OSSAccessKeyId=LTAI5tSEGjGp5wixZgHLc3bV&Expires=4967059621&Signature=iecGwpNGNIIzz4gmH9GW9U%2FzEMU%3D",
                    "language": "en"
                }
            ]
        }
    ],
    "result": {
      "data": {
        "message": [],
        "usageMap": "{\"usage\":1}",
        "structData": {
          "message": [
            {
              "edit_info": {
                "goodsRects": {
                  "top": 0,
                  "left": 0,
                  "width": 749,
                  "height": 872
                },
                "languages": [
                  "en"
                ],
                "resultImageIds": [
                  "34148e96-429f-11f0-8340-00163e1272a3"
                ],
                "textAreas": [
                  {
                    "horizontalLayout": "center",
                    "verticalLayout": "center",
                    "color": "#000000",
                    "texts": [
                      {
                        "valid": true,
                        "horizontalLayout": "center",
                        "verticalLayout": "center",
                        "color": "#070604",
                        "ovis_err_msg": "| ovis time: 1.481",
                        "imageRect": {
                          "top": 120,
                          "left": 33,
                          "width": 496,
                          "degree": 0,
                          "height": 82
                        },
                        "fontsize": 38,
                        "language": "en",
                        "value": "Hilton Hotel Soft Mattress",
                        "textRect": {
                          "top": 136,
                          "left": 44,
                          "width": 474,
                          "degree": 0,
                          "height": 50
                        },
                        "trans_model_name": "MarcoVL2-8B-PicTrans",
                        "lineCount": 1
                      }
                    ],
                    "fontsize": 50,
                    "content": "希尔顿酒店软床垫",
                    "lineCount": 1
                  },
                  {
                    "horizontalLayout": "left",
                    "verticalLayout": "center",
                    "color": "#000000",
                    "texts": [
                      {
                        "valid": true,
                        "horizontalLayout": "center",
                        "verticalLayout": "center",
                        "color": "#504d48",
                        "ovis_err_msg": "| ovis time: 1.481",
                        "imageRect": {
                          "top": 205,
                          "left": 99,
                          "width": 331,
                          "degree": 0,
                          "height": 58
                        },
                        "fontsize": 28,
                        "language": "en",
                        "value": "Scientifically Blended Cotton Fabric",
                        "textRect": {
                          "top": 217,
                          "left": 23,
                          "width": 484,
                          "degree": 0,
                          "height": 34
                        },
                        "trans_model_name": "MarcoVL2-8B-PicTrans",
                        "lineCount": 1
                      }
                    ],
                    "fontsize": 35,
                    "content": "全棉面料科学配比",
                    "lineCount": 1
                  }
                ],
                "repairedUrl": "https://aib-image.oss-ap-southeast-1.aliyuncs.com/tufan%2F333084ee-429f-11f0-b032-00163e1272a3.png?OSSAccessKeyId=LTAI5tSEGjGp5wixZgHLc3bV&Expires=4965863197&Signature=KWiuBsDlV89BgCPschjiKuZkEKY%3D",
                "font": [
                  "AlibabaSans-Regular"
                ]
              },
              "src_image": "https://img.alicdn.com/imgextra/i1/1955749012/O1CN016P3Jas2GRY7vaevsK_!!1955749012.jpg",
              "result_list": [
                {
                  "fileUrl": "https://aib-image.oss-ap-southeast-1.aliyuncs.com/tufan%2F342bd452-429f-11f0-8340-00163e1272a3.jpg?OSSAccessKeyId=LTAI5tSEGjGp5wixZgHLc3bV&Expires=4965863199&Signature=xVFKFzxbdNdOW1d9IaZziqpukGA%3D",
                  "language": "en"
                }
              ]
            }
          ],
          "usageMap": "{\"usage\": 1}"
        }
      },
      "success": true,
      "requestId": "2166434317491911949008870e0da8"
    }
  },
  "resCode": 200,
  "resMessage": "success",
  "code": "0",
  "request_id": "2151fa1917491911951054017",
  "_trace_id_": "2166434317491911949008870e0da8"
}
```

### Errors <a href="#errors" id="errors"></a>

| <p><strong>Error</strong></p><p><strong>Code</strong></p> | **Error Message**                                  | **Description**                                                                                                                                                                                   |
| --------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 501                                                       | rate limit exceed                                  | The current interface has reached the current limit. Please contact us via [Discord](https://discord.gg/tvU7GFmpQR) or email us (aidgesales@alibaba-inc.com) to increase the current limit value. |
| 700                                                       | invalid input                                      | The format of the input parameters does not meet the requirements, and `resMessage` will return detailed fields that do not meet the requirements.                                                |
| 703                                                       | image size exceeds the limit                       | The image size in the request parameters exceeds the limit; the dimensions of the image must not exceed 4000x4000 pixels.                                                                         |
| 704                                                       | invalid image form                                 | The image format in the request parameters is invalid.                                                                                                                                            |
| 705                                                       | image file size exceeds the                        | The image size in the request parameters exceeds the limit; the image size must not exceed 10MB.                                                                                                  |
| 801                                                       | model failed                                       | Internal call exception,please contact us via [Discord](https://discord.gg/tvU7GFmpQR) or email us (aidgesales@alibaba-inc.com) for troubleshooting.                                              |
| 900                                                       | tpp url error                                      | Internal call exception,please contact us via [Discord](https://discord.gg/tvU7GFmpQR) or email us (aidgesales@alibaba-inc.com) for troubleshooting.                                              |
| 1000                                                      | content has sensitive data, please try other input | Content has sensitive data, please try other input.                                                                                                                                               |
| 1001                                                      | content control failed, please retry               | Content control failed, please retry. If the error persists,please contact us via [Discord](https://discord.gg/tvU7GFmpQR) or email us (aidgesales@alibaba-inc.com).                              |
| 1002                                                      | content risk filter failed, please contact us      | Content risk filter failed. Please contact us via [Discord](https://discord.gg/tvU7GFmpQR) or email us (aidgesales@alibaba-inc.com).                                                              |


# Image Translation Pro Version Layer Image Composition API Reference

<mark style="color:green;">`GET/POST`</mark>`/ai/image/translation/copmosite`&#x20;

#### Description

After obtaining parameters such as the position, color, and size of the translated text through [Image Translation Pro Version API Synchronous Interface](https://docs.aidc-ai.com/aidge-resource/api-reference/e-commerce-information-translation/image-translation/image-translation-pro-version-api-synchronous-interface) and making the necessary content modifications, you can call the Image Translation Pro Version Image Composition API interface to merge the layers and generate the final image.



### **Parameter Request**  <a href="#vjgn7" id="vjgn7"></a>

| Parameter | Parameter | Type   | Required | Description                                                                                                                                                                                                                                                                                                                |
| --------- | --------- | ------ | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| paramJson |           | Object | true     |                                                                                                                                                                                                                                                                                                                            |
|           | srcImage  | String | true     | The field `src_image` in the response of the Image Translation Pro Editor or Image Translation Pro Synchronous API.                                                                                                                                                                                                        |
|           | editInfo  | String | ture     | The field edit\_info (in JSON string format) in the response of the Image Translation Pro Editor or Image Translation Pro Synchronous API. Note: If modification of the text after image composition is required, please manually parse the edit\_info field and edit the value at edit\_info.textAreas.texts.value level. |

### Sample Request  <a href="#wvdlj" id="wvdlj"></a>

{% tabs %}
{% tab title="Java" %}
/\*The domain url of the API. \*for api purchased on global site. set api\_domain to "https://api.aidc-ai.com" For APIs purchased from the Chinese site, please us&#x65;_"https://cn-api.aidc-ai.com"domain (for api purchased on chinese site) set api\_domain to "https://cn-api.aidc-ai.com"_/ IopClient client = new IopClientImpl("domain url", "your key", "your secret"); IopRequest request = new IopRequest(); request.setApiName("/ai/image/translation/composite"); // If you have not purchased a formal quota, please add a trial flag; otherwise, you will receive a NoResource error code. // request.addHeaderParameter("x-iop-trial","true"); JSONObject jsonObject = new JSONObject(); jsonObject.put("editInfo", "{"goodsRects":{"top":238,"left":0,"width":631,"height":459},"languages":\["ja"],"resultImageIds":\["58538d2a-5258-11f0-b542-00163e0eb98a"],"textAreas":\[{"horizontalLayout":"left","verticalLayout":"center","color":"#000000","texts":\[{"valid":true,"horizontalLayout":"left","verticalLayout":"center","color":"#525252","ovis\_err\_msg":"| ovis time: 1.655","imageRect":{"top":78,"left":39,"width":429,"degree":0,"height":65},"fontsize":40,"language":"ja","value":"かわいいデザイン・クリアなベル音","textRect":{"top":91,"left":48,"width":700,"degree":0,"height":40},"trans\_model\_name":"MarcoVL2-8B-PicTrans","lineCount":1}],"fontsize":40,"content":"萌趣造型·清脆响铃","lineCount":1},{"horizontalLayout":"left","verticalLayout":"center","color":"#000000","texts":\[{"valid":true,"horizontalLayout":"left","verticalLayout":"center","color":"#a2a2a2","ovis\_err\_msg":"| ovis time: 1.655","imageRect":{"top":146,"left":39,"width":460,"degree":0,"height":76},"fontsize":27,"language":"ja","value":"揺れるとクリアなベル音が鳴り、子供の目を引きます","textRect":{"top":154,"left":45,"width":700,"degree":0,"height":60},"trans\_model\_name":"MarcoVL2-8B-PicTrans","lineCount":1}],"fontsize":23,"content":"在摇晃的时候，会发出清脆的铃铃声 吸引孩子目光","lineCount":2},{"horizontalLayout":"right","verticalLayout":"center","color":"#000000","texts":\[{"valid":true,"horizontalLayout":"right","verticalLayout":"center","color":"#098b98","ovis\_err\_msg":"| ovis time: 1.655","imageRect":{"top":224,"left":616,"width":160,"degree":0,"height":94},"fontsize":22,"language":"ja","value":"ベルベルベル","textRect":{"top":251,"left":629,"width":134,"degree":15.036200506607228,"height":40},"trans\_model\_name":"MarcoVL2-8B-PicTrans","lineCount":1}],"fontsize":41,"content":"铃铃铃","lineCount":1}],"repairedUrl":"https://aib-image.oss-ap-southeast-1.aliyuncs.com/tufan%2F574da64a-5258-11f0-a074-00163e0eb98a.png?OSSAccessKeyId=LTAI5tSEGjGp5wixZgHLc3bV\&Expires=4967591982\&Signature=Dm2Ck8zobVXmVluvfsRdjtbneo4%3D","font":\["AlibabaSansJP-Bold"]}"); jsonObject.put("srcImage", "https://img.alicdn.com/imgextra/i3/O1CN01HTDhDi28Fd85ZYs7H\_!!6000000007903-0-tps-800-800.jpg"); request.addApiParameter("paramJson", jsonObject.toString()); IopResponse response = client.execute(request); System.out.println(response.getBody()); Thread.sleep(10);

// Sample request parameters { "editInfo":"{"goodsRects":{"top":238,"left":0,"width":631,"height":459},"languages":\["ja"],"resultImageIds":\["58538d2a-5258-11f0-b542-00163e0eb98a"],"textAreas":\[{"horizontalLayout":"left","verticalLayout":"center","color":"#000000","texts":\[{"valid":true,"horizontalLayout":"left","verticalLayout":"center","color":"#525252","ovis\_err\_msg":"| ovis time: 1.655","imageRect":{"top":78,"left":39,"width":429,"degree":0,"height":65},"fontsize":40,"language":"ja","value":"かわいいデザイン・クリアなベル音","textRect":{"top":91,"left":48,"width":700,"degree":0,"height":40},"trans\_model\_name":"MarcoVL2-8B-PicTrans","lineCount":1}],"fontsize":40,"content":"萌趣造型·清脆响铃","lineCount":1},{"horizontalLayout":"left","verticalLayout":"center","color":"#000000","texts":\[{"valid":true,"horizontalLayout":"left","verticalLayout":"center","color":"#a2a2a2","ovis\_err\_msg":"| ovis time: 1.655","imageRect":{"top":146,"left":39,"width":460,"degree":0,"height":76},"fontsize":27,"language":"ja","value":"揺れるとクリアなベル音が鳴り、子供の目を引きます","textRect":{"top":154,"left":45,"width":700,"degree":0,"height":60},"trans\_model\_name":"MarcoVL2-8B-PicTrans","lineCount":1}],"fontsize":23,"content":"在摇晃的时候，会发出清脆的铃铃声 吸引孩子目光","lineCount":2},{"horizontalLayout":"right","verticalLayout":"center","color":"#000000","texts":\[{"valid":true,"horizontalLayout":"right","verticalLayout":"center","color":"#098b98","ovis\_err\_msg":"| ovis time: 1.655","imageRect":{"top":224,"left":616,"width":160,"degree":0,"height":94},"fontsize":22,"language":"ja","value":"ベルベルベル","textRect":{"top":251,"left":629,"width":134,"degree":15.036200506607228,"height":40},"trans\_model\_name":"MarcoVL2-8B-PicTrans","lineCount":1}],"fontsize":41,"content":"铃铃铃","lineCount":1}],"repairedUrl":"https://aib-image.oss-ap-southeast-1.aliyuncs.com/tufan%2F574da64a-5258-11f0-a074-00163e0eb98a.png?OSSAccessKeyId=LTAI5tSEGjGp5wixZgHLc3bV\&Expires=4967591982\&Signature=Dm2Ck8zobVXmVluvfsRdjtbneo4%3D","font":\["AlibabaSansJP-Bold"]}", "srcImage":"https://img.alicdn.com/imgextra/i3/O1CN01HTDhDi28Fd85ZYs7H\_!!6000000007903-0-tps-800-800.jpg" }
{% endtab %}
{% endtabs %}

### Parameters Response

<table><thead><tr><th>Parameter</th><th>Parameter</th><th width="128">Parameter</th><th>Type</th><th>Description</th></tr></thead><tbody><tr><td>imageResult</td><td></td><td></td><td>Object</td><td>response result</td></tr><tr><td></td><td>code</td><td></td><td>number</td><td>response code</td></tr><tr><td></td><td>data</td><td></td><td>Object</td><td></td></tr><tr><td></td><td></td><td>imageUrl</td><td>String</td><td>layer merging result</td></tr><tr><td></td><td></td><td>usage</td><td>number</td><td>usage</td></tr><tr><td></td><td>requestId</td><td></td><td></td><td>request ID</td></tr><tr><td></td><td>success</td><td></td><td>boolean</td><td></td></tr><tr><td></td><td>message</td><td></td><td>String</td><td></td></tr><tr><td>resCode</td><td></td><td></td><td>Number</td><td>response code 200</td></tr><tr><td>resMessage</td><td></td><td></td><td>String</td><td>response message</td></tr><tr><td>request_id</td><td></td><td></td><td>String</td><td>request ID</td></tr><tr><td>_trace_id</td><td></td><td></td><td>String</td><td>Trace</td></tr></tbody></table>

### Sample Response  <a href="#hhacj" id="hhacj"></a>

{% tabs %}
{% tab title="JSON" %}
{ "resCode": 200, "resMessage": "success", "imageResult": { "code": 200, "data": { "imageUrl": "https://piccopilot.oss-accelerate.aliyuncs.com/compose/7c89c391-acb0-4ff4-8804-564c7f953cee.png?OSSAccessKeyId=LTAI5tR9CxJh5q35LYbhGAeT\&Expires=4967593669\&Signature=Hxrc5T%2BKn6Z8tR1qJRniZOQJnWg%3D", "usage": 0, "class": "com.aidc.service.api.client.image.dto.ImageGenResponse" }, "requestId": "0bb7408b17509216673995113e0e95", "success": true, "message": "success", "class": "com.aidc.service.api.client.common.Result" }, "code": "0", "request\_id": "2151fa1917509216676262651", "_trace\_id_": "0bb7408b17509216673995113e0e95" }
{% endtab %}
{% endtabs %}

### Errors <a href="#etacc" id="etacc"></a>

| Error Code | Error Message                                      | Description                                                                                                                                                                                       |
| ---------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 501        | rate limit exceed                                  | The current interface has reached the current limit. Please contact us via [Discord](https://discord.gg/tvU7GFmpQR) or email us (aidgesales@alibaba-inc.com) to increase the current limit value. |
| 700        | invalid input                                      | The format of the input parameters does not meet the requirements, and `resMessage` will return detailed fields that do not meet the requirements.                                                |
| 801        | model failed                                       | Internal call exception,please contact us via [Discord](https://discord.gg/tvU7GFmpQR) or email us (aidgesales@alibaba-inc.com) for troubleshooting.                                              |
| 900        | tpp url error                                      | Internal call exception,please contact us via [Discord](https://discord.gg/tvU7GFmpQR) or email us (aidgesales@alibaba-inc.com) for troubleshooting.                                              |
| 1000       | content has sensitive data, please try other input | Content has sensitive data, please try other input.                                                                                                                                               |
| 1001       | content control failed, please retry               | Content control failed, please retry.                                                                                                                                                             |
| 1002       | content risk filter failed, please contact us      | Content risk filter failed. Please contact us via [Discord](https://discord.gg/tvU7GFmpQR) or email us (aidgesales@alibaba-inc.com).                                                              |

