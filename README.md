> 以下內容及程式實現不是由我本人原創，而是基於以下專案的 fork 版本：
> - https://github.com/Cognitive-Creators-AI/claude-on-windows
> - https://gist.github.com/santolucito/728c2da6eff51113ddc4ad14a56594ab

在這個版本中，我將第二個檔案所做的改動整合到windows版本上，現在插入了適當的延遲來規避rate limit，同時也新增了多個指令中間的延遲
並將prompt cacheing也加入到windows版本，用以減少送出的token數量

---
# claude-on-windows
一個與Windows相容的[Anthropic電腦使用演示](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo)版本，經過修改可以在Windows上原生運行，無需Docker容器。

## ⚠️ 注意事項
電腦使用是一個測試版功能。請注意，電腦使用功能帶來的風險與標準API功能或聊天界面的風險有所不同。在使用電腦功能與互聯網互動時，這些風險會更加突出。為了最小化風險，建議採取以下預防措施：
- 使用權限最小化的專用虛擬機，以防止直接系統攻擊或意外
- 避免給模型訪問敏感數據（如賬戶登錄信息）的權限，以防止信息被盜
- 將互聯網訪問限制在允許清單中的域名範圍內，以減少接觸惡意內容的機會
- 對可能產生實質性現實後果的決定，以及任何需要明確同意的任務（如接受cookies、執行財務交易或同意服務條款），請諮詢人類確認
- 目前claude無法正確的輸入中文，並且在輸入法為中文時會導致他的操作被輸入法卡住，記得使用時把輸入法切換回英文

在某些情況下，Claude會執行在內容中找到的命令，即使這些命令與用戶的指示相衝突。例如，網頁上的指示或圖片中包含的指示可能會覆蓋用戶指示或導致Claude出錯。我們建議採取預防措施，將Claude與敏感數據和操作隔離，以避免與提示注入相關的風險。

**實驗性軟件 - 使用風險自負**。本軟件按"原樣"提供，不提供任何形式的保證。作者和貢獻者對使用本軟件可能造成的任何損害或系統問題概不負責。

## 設置
1. 克隆此存儲庫
2. 創建虛擬環境：`python -m venv venv`
3. 激活虛擬環境：`.\venv\Scripts\activate`
4. 安裝依賴：`python -m pip install -r requirements.txt`
5. 在`.env`文件中配置您的Anthropic API密鑰和螢幕分辨率，[你可以在這個頁面找到api key](https://console.anthropic.com/dashboard)
6. 運行應用程序：`python -m streamlit run run.py`
7. 你使用的python建議為3.11.x 較新或較舊的版本可能會有一些神秘的相容問題
8. 若是遇到環境上的問題，[可以參考這部影片](https://www.youtube.com/watch?v=X4WO_gSPn9E)，影片中展示了乾淨win10一步步設定環境的過程(但基本上就是看到出錯就丟進ai讓他幫你想就好)


## 使用方法
1. 啟動應用程序後，在瀏覽器中打開http://localhost:8501
2. 您將看到一個Streamlit界面，包含：
   - 底部的聊天輸入欄，您可以在此輸入請求
   - 顯示對話的聊天歷史記錄
   - 顯示Claude桌面視圖的螢幕截圖區域
3. 您可以要求Claude執行各種電腦任務，例如：
   - 創建或編輯文件
   - 運行命令
   - 與應用程序互動
   - 分析螢幕內容
4. Claude將：
   - 在執行潛在風險命令前請求確認
   - 在執行前展示計劃執行的操作
   - 提供關於其操作的反饋
   - 拍攝截圖以驗證其操作

**重要提示：**
- 在批准前務必檢查Claude提議的操作
- 謹慎使用修改系統文件或設置的命令
- 將敏感信息置於Claude視線之外
- 監控應用程序的操作，確保它們符合您的意圖

## 螢幕分辨率
可以使用`.env`文件中的環境變量`WIDTH`和`HEIGHT`來設置螢幕大小。我們不建議發送高於XGA/WXGA分辨率的截圖，以避免圖像調整大小相關的問題。

## 致謝
本項目基於[Anthropic的電腦使用演示](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo)，並經過修改以在Windows系統上原生運行，無需Docker容器。原始實現的所有功勞歸功於Anthropic。

---

# claude-on-windows
A Windows-compatible version of [Anthropic's Computer Use Demo](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo), modified to run natively on Windows without requiring Docker containers.

## ⚠️ Caution
Computer use is a beta feature. Please be aware that computer use poses unique risks that are distinct from standard API features or chat interfaces. These risks are heightened when using computer use to interact with the internet. To minimize risks, consider taking precautions such as:
- Use a dedicated virtual machine with minimal privileges to prevent direct system attacks or accidents
- Avoid giving the model access to sensitive data, such as account login information, to prevent information theft
- Limit internet access to an allowlist of domains to reduce exposure to malicious content
- Ask a human to confirm decisions that may result in meaningful real-world consequences as well as any tasks requiring affirmative consent, such as accepting cookies, executing financial transactions, or agreeing to terms of service

In some circumstances, Claude will follow commands found in content even if it conflicts with the user's instructions. For example, instructions on webpages or contained in images may override user instructions or cause Claude to make mistakes. We suggest taking precautions to isolate Claude from sensitive data and actions to avoid risks related to prompt injection.

**EXPERIMENTAL SOFTWARE - USE AT YOUR OWN RISK**. This software is provided "as is", without warranty of any kind. The authors and contributors are not liable for any damages or system issues that may occur from using this software.

## Setup
1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `.\venv\Scripts\activate`
4. Install dependencies: `python -m pip install -r requirements.txt`
5. Configure your `.env` file with your Anthropic API key and screen resolution
6. Run the application: `python -m streamlit run run.py`

## Usage
1. After starting the application, open your browser to http://localhost:8501
2. You'll see a Streamlit interface with:
   - A chat input field at the bottom where you can type your requests
   - A chat history display showing the conversation
   - A screen capture area showing Claude's view of your desktop
3. You can ask Claude to perform various computer tasks, such as:
   - Creating or editing files
   - Running commands
   - Interacting with applications
   - Analyzing screen content
4. Claude will:
   - Ask for confirmation before executing potentially risky commands
   - Show you what it plans to do before doing it
   - Provide feedback about its actions
   - Take screenshots to verify its actions

**Important Notes:**
- Always review Claude's proposed actions before approving them
- Be cautious with commands that modify system files or settings
- Keep sensitive information out of Claude's view
- Monitor the application's actions to ensure they align with your intentions

## Screen Resolution
Environment variables `WIDTH` and `HEIGHT` in the `.env` file can be used to set the screen size. We do not recommend sending screenshots in resolutions above XGA/WXGA to avoid issues related to image resizing.

## Attribution
This project is based on [Anthropic's Computer Use Demo](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo) and has been modified to run natively on Windows systems without requiring Docker containers. All credit for the original implementation goes to Anthropic.
