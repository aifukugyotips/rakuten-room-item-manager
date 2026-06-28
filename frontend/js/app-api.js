/**
 * 楽天ROOMアイテムマネージャー
 * Alpine.js アプリケーションロジック (API接続版)
 */

// API Base URL
const API_BASE_URL = 'http://localhost:8000/api';

/**
 * HTTP リクエストを送信
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    };

    try {
        const response = await fetch(url, config);

        // 204 No Content の場合
        if (response.status === 204) {
            return null;
        }

        // レスポンスがJSONかどうかチェック
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();

            if (!response.ok) {
                // data.detailが文字列でない場合はJSON文字列化
                let errorMessage;
                if (typeof data.detail === 'string') {
                    errorMessage = data.detail;
                } else if (data.detail) {
                    errorMessage = JSON.stringify(data.detail);
                } else {
                    errorMessage = `HTTP error! status: ${response.status}`;
                }
                throw new Error(errorMessage);
            }

            return data;
        } else {
            // JSON以外のレスポンス（HTMLエラーページなど）
            const text = await response.text();
            console.error('Non-JSON response:', text);
            throw new Error(`HTTP error! status: ${response.status} - ${text.substring(0, 100)}`);
        }
    } catch (error) {
        console.error('API Error:', error);
        // エラーオブジェクトをそのまま投げるとmessageが表示されるはず
        throw error;
    }
}

function roomManager() {
    return {
        // 現在の画面
        currentView: 'setup', // setup, items, profile-basic, profile-ai, trash

        // 設定メニューの開閉
        settingsMenuOpen: false,

        // 選択中のAIプロバイダー（ブラウザ状態管理のみ）
        selectedAIProvider: '',

        // 利用可能なAIプロバイダー
        availableProviders: [],

        // プロフィールデータ
        profile: {
            id: null,
            room_name: '',
            room_id: '',
            target_audience: '',
            room_direction: '',
            room_theme: '',
            tone_manner: '親しみやすい',
            posting_style: '',
            ng_words: '',
            // AI連携設定
            ai_enabled: false,
            ai_provider_openai_key: '',
            ai_provider_openai_model: '',
            ai_provider_gemini_key: '',
            ai_provider_gemini_model: '',
            ai_provider_perplexity_key: '',
            ai_provider_perplexity_model: '',
            ai_provider_claude_key: '',
            ai_provider_claude_model: ''
        },
        originalProfile: null,

        // 商品データ
        items: [],

        // ゴミ箱データ
        trashItems: [],
        trashCount: 0,

        // フィルタ状態
        searchQuery: '',
        hashtagQuery: '',
        statusFilter: '全て',
        priorityFilter: '全て',

        // 表示モード
        viewMode: 'grid', // 'grid', 'list', 'compact', or 'calendar'

        // カレンダー表示用の状態
        calendarYear: new Date().getFullYear(),
        calendarMonth: new Date().getMonth() + 1, // 1-12
        selectedDate: null, // フィルタリング用の選択日付（YYYY-MM-DD形式）

        // 商品登録・編集モーダル
        itemModalOpen: false,
        editingItem: null,
        originalItemForm: null,
        itemForm: {},

        // 新規登録時の画像一時保持
        pendingImageFile: null,
        pendingImagePreview: null,

        // クロップモーダル
        showCropModal: false,
        cropperInstance: null,
        pendingCropCallback: null,

        // 商品詳細モーダル
        itemDetailModalOpen: false,
        detailItem: null,

        // ローディング状態
        loading: false,
        loadingMessage: '',
        error: null,
        aiGenerating: false,

        // ショートカットヘルプモーダル
        shortcutHelpModalOpen: false,

        // 商品フォーカスナビゲーション
        focusMode: false,
        selectedItemIndex: -1,
        lastSelectedIndex: -1,

        // 通知
        notifications: [],
        notificationId: 0,

        // 初期化
        async init() {
            this.loading = true;
            try {
                // APIからデータを読み込み
                await this.loadFromAPI();

                // URLハッシュから画面を復元、なければプロフィールの有無で判断
                const hash = window.location.hash;
                if (hash) {
                    this.syncFromURL();
                } else if (this.profile.id) {
                    this.navigateTo('items');
                } else {
                    this.navigateTo('setup');
                }

                // ブラウザの戻る/進むボタンに対応
                window.addEventListener('hashchange', () => {
                    this.syncFromURL();
                });

                // グローバルキーボードショートカット
                window.addEventListener('keydown', (e) => {
                    this.handleGlobalKeydown(e);
                });

            } catch (error) {
                console.error('初期化エラー:', error);
                // エラーでもセットアップ画面は表示する
                this.navigateTo('setup');
            } finally {
                this.loading = false;
            }
        },

        // APIからデータを読み込み
        async loadFromAPI() {
            try {
                // 利用可能なAIプロバイダーを取得
                const providersData = await apiRequest('/ai/available-providers');
                this.availableProviders = providersData.providers || [];

                // デフォルトのプロバイダーを設定（まだ選択されていない場合）
                if (this.availableProviders.length > 0 && this.selectedAIProvider === '') {
                    this.selectedAIProvider = this.availableProviders[0].id;
                }

                // プロフィールを取得
                const profileData = await apiRequest('/profile');
                if (profileData) {
                    this.profile = profileData;
                }

                // プロフィールがある場合のみ商品を取得
                if (this.profile.id) {
                    const itemsData = await apiRequest('/items');
                    this.items = itemsData.items || [];

                    // 統計情報を取得してゴミ箱カウントを更新
                    const stats = await apiRequest('/items/stats/summary');
                    this.trashCount = stats.trash_count || 0;
                }
            } catch (error) {
                console.error('データ読み込みエラー:', error);
                throw error;
            }
        },

        // 基本情報設定画面を開く
        openBasicSettings() {
            this.originalProfile = { ...this.profile };
            this.navigateTo('profile-basic');
            this.settingsMenuOpen = false;
        },

        // AI連携設定画面を開く
        openAISettings() {
            this.originalProfile = { ...this.profile };
            this.navigateTo('profile-ai');
            this.settingsMenuOpen = false;
        },

        // プロフィールに変更があるかチェック
        hasProfileChanges() {
            if (!this.originalProfile) {
                return false;
            }
            return JSON.stringify(this.originalProfile) !== JSON.stringify(this.profile);
        },

        // プロフィール編集画面を閉じる
        closeProfileEdit() {
            if (this.hasProfileChanges()) {
                if (!confirm('保存していない変更があります。破棄しますか？')) {
                    return;
                }
                this.profile = { ...this.originalProfile };
            }
            this.originalProfile = null;
            this.navigateTo('items');
        },

        // プロフィール保存
        async saveProfile() {
            this.loading = true;
            this.loadingMessage = '保存中...';
            this.error = null;

            try {
                let savedProfile;

                if (this.profile.id) {
                    // 更新
                    savedProfile = await apiRequest(`/profile/${this.profile.id}`, {
                        method: 'PUT',
                        body: JSON.stringify(this.profile),
                    });
                } else {
                    // 新規作成
                    savedProfile = await apiRequest('/profile', {
                        method: 'POST',
                        body: JSON.stringify(this.profile),
                    });
                }

                this.profile = savedProfile;
                this.originalProfile = null;
                this.navigateTo('items');
                this.showNotification('プロフィールを保存しました', 'success');
            } catch (error) {
                this.error = error.message;
                this.showNotification('エラー: ' + error.message, 'error');
            } finally {
                this.loading = false;
                this.loadingMessage = '';
            }
        },

        // 初期設定をスキップ
        skipSetup() {
            this.profile.room_name = '楽天ROOM';
            this.navigateTo('items');
        },

        // 商品登録・編集モーダルを開く
        openItemModal(item) {
            this.editingItem = item;

            // 配列フィールドのディープコピー
            this.itemForm = item ? {
                ...item,
                posted_at_history: item.posted_at_history ? [...item.posted_at_history] : []
            } : {
                name: '',
                category: 'ガジェット',
                sub_category: '',
                brand_model: '',
                usage_scene: '',
                frequency: '毎日',
                favorite_points: '',
                seasonality: '通年',
                has_photo: false,
                photo_path: '',
                is_original_photo: false,
                has_item: false,
                priority: 3,
                rakuten_url: '',
                room_url: '',
                memo: '',
                description: '',
                status: '未投稿',
                posted_at_history: []
            }

            // originalItemFormには元のitemをそのままコピー（キャンセル時に復元するため）
            this.originalItemForm = item ? {
                ...item,
                posted_at_history: item.posted_at_history ? [...item.posted_at_history] : []
            } : null;

            this.itemModalOpen = true;

            // モーダルが開いた後、スクロール位置を一番上にリセット
            this.$nextTick(() => {
                const modalContent = document.querySelector('[x-show="itemModalOpen"] .overflow-y-auto');
                if (modalContent) {
                    modalContent.scrollTop = 0;
                }
            });
        },

        // 投稿履歴を追加
        addPostedAtHistory() {
            if (!this.itemForm.posted_at_history) {
                this.itemForm.posted_at_history = [];
            }
            if (this.itemForm.posted_at_history.length < 3) {
                // 現在の日時をISO形式で追加
                this.itemForm.posted_at_history.push(new Date().toISOString());
            }
        },

        // 投稿履歴を削除
        removePostedAtHistory(index) {
            if (this.itemForm.posted_at_history && this.itemForm.posted_at_history.length > index) {
                this.itemForm.posted_at_history.splice(index, 1);
            }
        },

        // 投稿履歴を更新
        updatePostedAtHistory(index, value) {
            if (this.itemForm.posted_at_history && this.itemForm.posted_at_history.length > index) {
                // datetime-local形式（JST）からUTC ISO形式に変換
                // datetime-local は "2026-02-16T03:36" のような形式（タイムゾーン情報なし）
                // これをJSTとして扱い、UTCに変換する
                const jstDate = new Date(value + ':00+09:00'); // JSTとして明示的に指定
                this.itemForm.posted_at_history[index] = jstDate.toISOString();
            }
        },

        // UTC日時をJST（日本時間）のdatetime-local形式にフォーマット
        formatDateTimeLocal(dateString) {
            if (!dateString) return '';

            // 'Z' がない場合は追加（UTC として明示的に扱う）
            // バックエンドから isoformat() で返される値に 'Z' がないため
            let utcString = dateString;
            if (!dateString.endsWith('Z') && !dateString.includes('+') && !dateString.includes('-', 10)) {
                utcString = dateString + 'Z';
            }

            const date = new Date(utcString);

            // JSTの日時を取得
            const jstString = date.toLocaleString('ja-JP', {
                timeZone: 'Asia/Tokyo',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });

            // "2026/02/16 03:36" -> "2026-02-16T03:36" に変換
            const [datePart, timePart] = jstString.split(' ');
            const formattedDate = datePart.replace(/\//g, '-');
            return `${formattedDate}T${timePart}`;
        },

        // UTC日時を日本時間の日付文字列に変換（YYYY/MM/DD形式）
        formatJSTDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleString('ja-JP', {
                timeZone: 'Asia/Tokyo',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            }).replace(/\//g, '/');
        },

        // フォームに変更があるかチェック
        hasFormChanges() {
            if (!this.editingItem || !this.originalItemForm) {
                // 新規作成の場合、何か入力されていればtrueを返す
                if (!this.editingItem) {
                    return this.itemForm.name ||
                           this.itemForm.category !== 'ガジェット' ||
                           this.itemForm.brand_model ||
                           this.itemForm.usage_scene ||
                           this.itemForm.frequency !== '毎日' ||
                           this.itemForm.favorite_points ||
                           this.itemForm.seasonality !== '通年' ||
                           this.itemForm.priority !== 3 ||
                           this.itemForm.rakuten_url ||
                           this.itemForm.room_url ||
                           this.itemForm.memo ||
                           this.itemForm.description ||
                           this.itemForm.status !== '未投稿';
                }
                return false;
            }

            // 編集の場合、元の値と比較
            const formCopy = { ...this.itemForm };
            const originalCopy = { ...this.originalItemForm };

            return JSON.stringify(originalCopy) !== JSON.stringify(formCopy);
        },

        // 商品登録・編集モーダルを閉じる
        closeItemModal(force = false) {
            // 変更があれば確認（強制クローズの場合はスキップ）
            if (!force && this.hasFormChanges()) {
                let message = '保存していない変更があります。破棄しますか？';
                if (this.editingItem) {
                    message += '\n\n※ 画像のアップロード・削除は既に保存されています。';
                }
                if (!confirm(message)) {
                    return;
                }
            }

            if (this.editingItem && this.originalItemForm) {
                const index = this.items.findIndex(i => i.id === this.editingItem.id);
                if (index !== -1) {
                    this.items[index] = { ...this.originalItemForm };
                }
            }
            this.itemModalOpen = false;
            this.editingItem = null;
            this.originalItemForm = null;
            this.pendingImageFile = null;
            this.pendingImagePreview = null;
            this.itemForm = {};

            // フォーカスモードを復元（前に選択していた商品にフォーカスを戻す）
            if (this.lastSelectedIndex >= 0 && this.lastSelectedIndex < this.filteredItems.length) {
                this.selectedItemIndex = this.lastSelectedIndex;
                this.focusMode = true;
                this.scrollToSelectedItem();
            }
        },

        // 商品詳細モーダルを開く
        openItemDetailModal(item) {
            this.detailItem = item;
            this.itemDetailModalOpen = true;

            // モーダルが開いた後、スクロール位置を一番上にリセット
            this.$nextTick(() => {
                const modalContent = document.querySelector('[x-show="itemDetailModalOpen"] .overflow-y-auto');
                if (modalContent) {
                    modalContent.scrollTop = 0;
                }
            });
        },

        // 商品詳細モーダルを閉じる
        closeItemDetailModal() {
            this.itemDetailModalOpen = false;
            this.detailItem = null;
        },

        // 詳細モーダルから編集モーダルへ切り替え
        editFromDetail() {
            const item = this.detailItem;
            this.closeItemDetailModal();
            this.openItemModal(item);
        },

        // 商品を保存
        async saveItem() {
            this.loading = true;
            this.loadingMessage = '保存中...';
            this.error = null;

            try {
                const formData = { ...this.itemForm };
                let savedItem;

                if (this.editingItem) {
                    // 更新
                    savedItem = await apiRequest(`/items/${this.editingItem.id}`, {
                        method: 'PUT',
                        body: JSON.stringify(formData),
                    });

                    // ローカルの配列を更新
                    const index = this.items.findIndex(i => i.id === this.editingItem.id);
                    if (index !== -1) {
                        this.items[index] = savedItem;
                    }

                    this.showNotification('商品を更新しました', 'success');
                } else {
                    // 新規作成
                    savedItem = await apiRequest('/items', {
                        method: 'POST',
                        body: JSON.stringify(formData),
                    });

                    // ローカルの配列に追加
                    this.items.push(savedItem);

                    // 新規登録時に画像が選択されていた場合、自動的にアップロード
                    if (this.pendingImageFile) {
                        try {
                            const updatedItem = await this.uploadImage(savedItem.id, this.pendingImageFile, true);
                            // 配列内のアイテムを更新
                            const index = this.items.findIndex(i => i.id === savedItem.id);
                            if (index !== -1) {
                                this.items[index] = updatedItem;
                            }
                            this.showNotification('商品と画像を登録しました', 'success');
                        } catch (error) {
                            // 画像アップロードが失敗しても商品は登録されているので続行
                            this.showNotification('商品を登録しました\n（画像のアップロードに失敗しました）', 'warning');
                        }
                    } else {
                        this.showNotification('商品を登録しました', 'success');
                    }
                }

                this.originalItemForm = null;
                this.closeItemModal(true); // 保存成功後は確認ダイアログをスキップ
            } catch (error) {
                this.error = error.message;
                this.showNotification('エラー: ' + error.message, 'error');
            } finally {
                this.loading = false;
                this.loadingMessage = '';
            }
        },

        // 商品をゴミ箱へ移動
        async deleteItem(id) {
            if (!confirm('この商品をゴミ箱に移動しますか？')) {
                return;
            }

            this.loading = true;
            this.loadingMessage = 'ゴミ箱へ移動中...';
            this.error = null;

            try {
                await apiRequest(`/items/${id}`, {
                    method: 'DELETE',
                });

                // ローカルの配列から削除
                this.items = this.items.filter(item => item.id !== id);

                // ゴミ箱カウントを更新
                this.trashCount++;

                this.showNotification('商品をゴミ箱に移動しました', 'success');
            } catch (error) {
                this.error = error.message;
                this.showNotification('エラー: ' + error.message, 'error');
            } finally {
                this.loading = false;
                this.loadingMessage = '';
            }
        },

        // ゴミ箱画面を開く
        async openTrash() {
            this.navigateTo('trash');
            await this.loadTrashItems();
        },

        // ゴミ箱の商品を取得
        async loadTrashItems() {
            this.loading = true;
            this.error = null;

            try {
                const data = await apiRequest('/items/trash');
                this.trashItems = data.items || [];
            } catch (error) {
                this.error = error.message;
                this.showNotification('エラー: ' + error.message, 'error');
            } finally {
                this.loading = false;
            }
        },

        // 商品を復元
        async restoreItem(id) {
            if (!confirm('この商品を復元しますか？')) {
                return;
            }

            this.loading = true;
            this.loadingMessage = '復元中...';
            this.error = null;

            try {
                const restoredItem = await apiRequest(`/items/${id}/restore`, {
                    method: 'POST',
                });

                // ゴミ箱から削除
                this.trashItems = this.trashItems.filter(item => item.id !== id);

                // 通常の商品配列に追加
                this.items.push(restoredItem);

                // ゴミ箱カウントを更新
                this.trashCount--;

                this.showNotification('商品を復元しました', 'success');
            } catch (error) {
                this.error = error.message;
                this.showNotification('エラー: ' + error.message, 'error');
            } finally {
                this.loading = false;
                this.loadingMessage = '';
            }
        },

        // 商品を完全削除
        async deletePermanent(id) {
            if (!confirm('この商品を完全に削除しますか？\nこの操作は取り消せません。')) {
                return;
            }

            this.loading = true;
            this.loadingMessage = '完全削除中...';
            this.error = null;

            try {
                await apiRequest(`/items/${id}/permanent`, {
                    method: 'DELETE',
                });

                // ゴミ箱から削除
                this.trashItems = this.trashItems.filter(item => item.id !== id);

                // ゴミ箱カウントを更新
                this.trashCount--;

                this.showNotification('商品を完全に削除しました', 'success');
            } catch (error) {
                this.error = error.message;
                this.showNotification('エラー: ' + error.message, 'error');
            } finally {
                this.loading = false;
                this.loadingMessage = '';
            }
        },

        // 画像をアップロード
        // 画像選択時の処理（クロップモーダルを経由してからアップロード）
        async handleImageSelect(event) {
            const file = event.target.files[0];
            if (!file) return;
            event.target.value = '';

            const afterCrop = async (croppedFile) => {
                if (this.editingItem) {
                    try {
                        const updatedItem = await this.uploadImage(this.editingItem.id, croppedFile);
                        this.itemForm.has_photo = updatedItem.has_photo;
                        this.itemForm.photo_path = updatedItem.photo_path;
                        if (this.originalItemForm) {
                            this.originalItemForm.has_photo = updatedItem.has_photo;
                            this.originalItemForm.photo_path = updatedItem.photo_path;
                        }
                    } catch (error) {
                        // エラーはuploadImage内で処理される
                    }
                } else {
                    this.pendingImageFile = croppedFile;
                    const reader = new FileReader();
                    reader.onload = (e) => { this.pendingImagePreview = e.target.result; };
                    reader.readAsDataURL(croppedFile);
                }
            };

            this.openCropModal(file, afterCrop);
        },

        openCropModal(file, callback) {
            this.pendingCropCallback = callback;
            const reader = new FileReader();
            reader.onload = (e) => {
                const originalSrc = e.target.result;
                const tmpImg = new Image();
                tmpImg.onload = () => {
                    // 大きい画像をそのまま Cropper に渡すとブラウザが固まるため
                    // 1200px を超える場合は先にリサイズする（出力は 1024x1024 なので十分な解像度）
                    const MAX = 1200;
                    let src = originalSrc;
                    if (tmpImg.naturalWidth > MAX || tmpImg.naturalHeight > MAX) {
                        const ratio = Math.min(MAX / tmpImg.naturalWidth, MAX / tmpImg.naturalHeight);
                        const resizeCanvas = document.createElement('canvas');
                        resizeCanvas.width  = Math.round(tmpImg.naturalWidth  * ratio);
                        resizeCanvas.height = Math.round(tmpImg.naturalHeight * ratio);
                        resizeCanvas.getContext('2d').drawImage(tmpImg, 0, 0, resizeCanvas.width, resizeCanvas.height);
                        src = resizeCanvas.toDataURL('image/jpeg', 0.92);
                    }
                    // Alpine.js の x-show に頼らず vanilla JS で表示（スコープ問題を回避）
                    document.getElementById('cropModal').style.display = 'flex';
                    const img = document.getElementById('cropperImage');
                    if (!img) return;
                    if (this.cropperInstance) {
                        this.cropperInstance.destroy();
                        this.cropperInstance = null;
                    }
                    img.src = src;
                    this.cropperInstance = new Cropper(img, {
                        aspectRatio: 1,
                        viewMode: 0,
                        autoCropArea: 0.9,
                        movable: true,
                        zoomable: true,
                        rotatable: false,
                        scalable: false,
                    });
                };
                tmpImg.src = originalSrc;
            };
            reader.readAsDataURL(file);
        },

        async confirmCrop() {
            if (!this.cropperInstance) return;
            // モーダルを先に閉じてからローディング表示
            // （モーダルが全面を覆っているとローディングが隠れて見えないため）
            document.getElementById('cropModal').style.display = 'none';
            this.loading = true;
            this.loadingMessage = '画像を切り抜き中...';
            const cropper = this.cropperInstance;
            const callback = this.pendingCropCallback;
            this.cropperInstance = null;
            this.pendingCropCallback = null;
            // Alpine がローディング表示を描画するまで待つ
            await new Promise(r => setTimeout(r, 80));
            try {
                const canvas = cropper.getCroppedCanvas({ width: 1024, height: 1024 });
                cropper.destroy();
                if (!canvas) {
                    this.loading = false;
                    this.error = '画像の切り抜きに失敗しました。別の画像で試してください。';
                    return;
                }
                const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', 0.92));
                if (!blob) {
                    this.loading = false;
                    this.error = '画像の変換に失敗しました。';
                    return;
                }
                const croppedFile = new File([blob], 'photo_cropped.jpeg', { type: 'image/jpeg' });
                if (callback) {
                    await callback(croppedFile);
                }
            } catch (e) {
                this.error = '画像処理中にエラーが発生しました。';
            } finally {
                this.loading = false;
            }
        },

        cancelCrop() {
            document.getElementById('cropModal').style.display = 'none';
            if (this.cropperInstance) {
                this.cropperInstance.destroy();
                this.cropperInstance = null;
            }
            this.pendingCropCallback = null;
        },

        async uploadImage(itemId, file, suppressNotification = false) {
            this.loading = true;
            this.loadingMessage = '画像アップロード中...';
            this.error = null;

            try {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch(`${API_BASE_URL}/items/${itemId}/upload-image`, {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.detail || '画像のアップロードに失敗しました');
                }

                const data = await response.json();

                // ローカルの配列を更新
                const index = this.items.findIndex(i => i.id === itemId);
                if (index !== -1) {
                    this.items[index] = data.item;
                }

                if (!suppressNotification) {
                    this.showNotification('画像をアップロードしました', 'success');
                }
                return data.item;
            } catch (error) {
                this.error = error.message;
                this.showNotification('エラー: ' + error.message, 'error');
                throw error;
            } finally {
                this.loading = false;
                this.loadingMessage = '';
            }
        },

        // 画像を削除
        async deleteImage(itemId) {
            if (!confirm('この画像を削除しますか？')) {
                return;
            }

            this.loading = true;
            this.loadingMessage = '画像削除中...';
            this.error = null;

            try {
                const data = await apiRequest(`/items/${itemId}/image`, {
                    method: 'DELETE',
                });

                // ローカルの配列を更新
                const index = this.items.findIndex(i => i.id === itemId);
                if (index !== -1) {
                    this.items[index] = data.item;
                }

                this.showNotification('画像を削除しました', 'success');
            } catch (error) {
                this.error = error.message;
                this.showNotification('エラー: ' + error.message, 'error');
                throw error;
            } finally {
                this.loading = false;
                this.loadingMessage = '';
            }
        },

        // CSVエクスポート
        async exportCSV() {
            try {
                const response = await fetch(`${API_BASE_URL}/export/csv`);

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('Export error:', errorText);
                    throw new Error('CSVのエクスポートに失敗しました');
                }

                // Blobとしてデータを取得
                const blob = await response.blob();
                console.log('Blob size:', blob.size, 'type:', blob.type);

                if (blob.size === 0) {
                    throw new Error('ダウンロードするデータがありません');
                }

                // ダウンロード用のリンクを作成
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;

                // ファイル名にタイムスタンプを追加
                const now = new Date();
                const timestamp = now.getFullYear() +
                    String(now.getMonth() + 1).padStart(2, '0') +
                    String(now.getDate()).padStart(2, '0') + '_' +
                    String(now.getHours()).padStart(2, '0') +
                    String(now.getMinutes()).padStart(2, '0') +
                    String(now.getSeconds()).padStart(2, '0');
                const filename = `rakuten_room_items_${timestamp}.csv`;

                a.download = filename;
                document.body.appendChild(a);
                a.click();

                // クリーンアップ
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }, 100);

                // ブラウザの標準ダウンロード機能が動作するため、通知は不要
            } catch (error) {
                console.error('Export CSV error:', error);
                this.showNotification('エラー: ' + error.message, 'error');
            }
        },

        // CSVインポート
        async importCSV(file) {
            this.loading = true;
            this.loadingMessage = 'CSVインポート中...';
            this.error = null;

            try {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch(`${API_BASE_URL}/export/csv/import`, {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.detail || 'CSVのインポートに失敗しました');
                }

                const data = await response.json();

                // データを再読み込み
                await this.loadFromAPI();

                let message = data.message;
                let type = 'success';
                if (data.errors && data.errors.length > 0) {
                    message += '\n\nエラー:\n' + data.errors.join('\n');
                    type = 'warning';
                }
                this.showNotification(message, type);
            } catch (error) {
                this.error = error.message;
                this.showNotification('エラー: ' + error.message, 'error');
            } finally {
                this.loading = false;
                this.loadingMessage = '';
            }
        },

        // フィルタをクリア
        clearFilters() {
            this.searchQuery = '';
            this.statusFilter = '全て';
            this.priorityFilter = '全て';
        },

        // 通知を表示
        showNotification(message, type = 'info', duration = 5000) {
            const id = this.notificationId++;
            const notification = {
                id: id,
                message: message,
                type: type, // 'success', 'error', 'info', 'warning'
                show: true
            };

            this.notifications.push(notification);

            // 指定時間後に自動的に削除
            setTimeout(() => {
                this.removeNotification(id);
            }, duration);
        },

        // 通知を削除
        removeNotification(id) {
            const index = this.notifications.findIndex(n => n.id === id);
            if (index !== -1) {
                this.notifications[index].show = false;
                // アニメーション後に配列から削除
                setTimeout(() => {
                    this.notifications = this.notifications.filter(n => n.id !== id);
                }, 300);
            }
        },

        // 入力フォームにフォーカスがあるかチェック
        isInputFocused() {
            const activeElement = document.activeElement;
            if (!activeElement) return false;
            const tagName = activeElement.tagName.toLowerCase();
            return tagName === 'input' || tagName === 'textarea' || tagName === 'select';
        },

        // グローバルキーボードショートカットハンドラ
        handleGlobalKeydown(e) {
            // モーダルが開いている場合はスキップ（モーダル内のショートカットが優先）
            if (this.itemModalOpen || this.itemDetailModalOpen) {
                return;
            }

            // ショートカットヘルプモーダルが開いている場合はESCのみ処理
            if (this.shortcutHelpModalOpen) {
                if (e.key === 'Escape') {
                    this.shortcutHelpModalOpen = false;
                    e.preventDefault();
                }
                return;
            }

            // 商品一覧画面でのみ有効
            if (this.currentView !== 'items') {
                return;
            }

            // 入力フォームにフォーカスがある場合は無効
            const isInputFocused = this.isInputFocused();

            // ESCキー - フォーカスモードON/OFF
            if (e.key === 'Escape' && !isInputFocused) {
                if (this.focusMode) {
                    // フォーカスモードOFF
                    this.exitFocusMode();
                } else {
                    // フォーカスモードON
                    this.enterFocusMode();
                }
                e.preventDefault();
                return;
            }

            // フォーカスモードがONの場合の矢印キー・Enterキー・Dキー
            if (this.focusMode && !isInputFocused) {
                // Enterキー - 選択中の商品を編集
                if (e.key === 'Enter') {
                    this.openSelectedItem();
                    e.preventDefault();
                    return;
                }

                // Dキー - 選択中の商品を削除（ゴミ箱へ移動）
                if (e.key === 'd' || e.key === 'D') {
                    this.deleteSelectedItem();
                    e.preventDefault();
                    return;
                }

                // 矢印キー - 商品間移動
                if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                    this.navigateItems(e.key);
                    e.preventDefault();
                    return;
                }
            }

            // ？キー - ショートカットヘルプ
            if (e.key === '?' && !isInputFocused) {
                this.shortcutHelpModalOpen = true;
                e.preventDefault();
                return;
            }

            // /キー - 検索フォーカス
            if (e.key === '/' && !isInputFocused) {
                const searchInput = document.querySelector('input[x-model="searchQuery"]');
                if (searchInput) {
                    // 商品ナビゲーションモードを解除してから検索窓にフォーカス
                    this.exitFocusMode();
                    searchInput.focus();
                    e.preventDefault();
                }
                return;
            }

            // Nキー - 新規商品登録
            if ((e.key === 'n' || e.key === 'N') && !isInputFocused) {
                this.openItemModal(null);
                e.preventDefault();
                return;
            }

            // 1〜4キー - 表示モード切り替え
            if (!isInputFocused) {
                const viewModes = {
                    '1': 'grid',
                    '2': 'list',
                    '3': 'compact',
                    '4': 'calendar'
                };
                if (viewModes[e.key]) {
                    this.viewMode = viewModes[e.key];
                    this.navigateTo('items', viewModes[e.key]);
                    e.preventDefault();
                    return;
                }
            }
        },

        // フォーカスモードON
        enterFocusMode(showNotification = true) {
            // カレンダーモードでは無効
            if (this.viewMode === 'calendar') {
                if (showNotification) {
                    this.showNotification('カレンダーモードでは商品ナビゲーションは使用できません', 'info', 3000);
                }
                return;
            }

            // 商品がない場合
            if (this.filteredItems.length === 0) {
                if (showNotification) {
                    this.showNotification('表示する商品がありません', 'info', 3000);
                }
                return;
            }

            this.focusMode = true;
            // 前回選択していた商品、範囲外なら最後の商品を選択
            if (this.lastSelectedIndex >= 0 && this.lastSelectedIndex < this.filteredItems.length) {
                this.selectedItemIndex = this.lastSelectedIndex;
            } else if (this.lastSelectedIndex >= 0) {
                // 範囲外（表示モード変更やフィルタ変更で商品数が減った場合）→ 最後の商品
                this.selectedItemIndex = this.filteredItems.length - 1;
            } else {
                // lastSelectedIndex が -1（初回）→ 最初の商品
                this.selectedItemIndex = 0;
            }
            this.scrollToSelectedItem();
            if (showNotification) {
                this.showNotification('商品ナビゲーション: 矢印キーで移動、Enterで編集、ESCで解除', 'info', 3000);
            }
        },

        // フォーカスモードOFF
        exitFocusMode() {
            this.focusMode = false;
            this.lastSelectedIndex = this.selectedItemIndex;
            this.selectedItemIndex = -1;
        },

        // 矢印キーで商品間移動
        navigateItems(key) {
            if (this.filteredItems.length === 0) return;

            const currentIndex = this.selectedItemIndex;
            let newIndex = currentIndex;

            if (this.viewMode === 'grid') {
                // グリッドビュー: 2D移動（3列想定）
                const columns = 3;
                const rows = Math.ceil(this.filteredItems.length / columns);

                if (key === 'ArrowUp') {
                    newIndex = currentIndex - columns;
                } else if (key === 'ArrowDown') {
                    newIndex = currentIndex + columns;
                } else if (key === 'ArrowLeft') {
                    newIndex = currentIndex - 1;
                } else if (key === 'ArrowRight') {
                    newIndex = currentIndex + 1;
                }
            } else {
                // リスト/コンパクトビュー: 1D移動
                if (key === 'ArrowUp') {
                    newIndex = currentIndex - 1;
                } else if (key === 'ArrowDown') {
                    newIndex = currentIndex + 1;
                }
            }

            // 範囲チェック
            if (newIndex < 0) {
                newIndex = 0;
            } else if (newIndex >= this.filteredItems.length) {
                newIndex = this.filteredItems.length - 1;
            }

            this.selectedItemIndex = newIndex;
            this.scrollToSelectedItem();
        },

        // 選択中の商品までスクロール
        scrollToSelectedItem() {
            this.$nextTick(() => {
                const selectedElement = document.querySelector(`[data-item-index="${this.selectedItemIndex}"]`);
                if (selectedElement) {
                    selectedElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            });
        },

        // 選択中の商品を編集
        openSelectedItem() {
            if (this.selectedItemIndex >= 0 && this.selectedItemIndex < this.filteredItems.length) {
                const item = this.filteredItems[this.selectedItemIndex];
                this.lastSelectedIndex = this.selectedItemIndex;
                this.focusMode = false;
                this.openItemModal(item);
            }
        },

        // 選択中の商品を削除（ゴミ箱へ移動）
        async deleteSelectedItem() {
            if (this.selectedItemIndex >= 0 && this.selectedItemIndex < this.filteredItems.length) {
                const item = this.filteredItems[this.selectedItemIndex];
                const currentIndex = this.selectedItemIndex;

                // 削除を実行
                await this.deleteItem(item.id);

                // フォーカスを次の商品に移動（削除後に商品が減るため調整）
                if (this.filteredItems.length > 0) {
                    // 削除後も同じインデックスに留まる（次の商品に自動的に移動）
                    if (currentIndex >= this.filteredItems.length) {
                        // 最後の商品を削除した場合は、新しい最後の商品を選択
                        this.selectedItemIndex = this.filteredItems.length - 1;
                    } else {
                        this.selectedItemIndex = currentIndex;
                    }
                    this.scrollToSelectedItem();
                } else {
                    // すべての商品を削除した場合はフォーカスモードを解除
                    this.exitFocusMode();
                }
            }
        },

        // AI で商品紹介文を生成
        async generateDescription() {
            if (!this.profile.ai_enabled) {
                this.showNotification('AI連携が有効になっていません。\n設定画面でAI連携を有効にしてください。', 'warning');
                return;
            }

            this.loading = true;
            this.aiGenerating = true;
            this.loadingMessage = 'AI生成中...';
            this.error = null;

            try {
                const data = await apiRequest('/items/generate-description', {
                    method: 'POST',
                    body: JSON.stringify({
                        item: this.itemForm,
                        profile: this.profile,
                        provider: this.selectedAIProvider
                    }),
                });

                this.itemForm.description = data.description;
                this.showNotification(`商品紹介文を生成しました\n(${data.provider} - ${data.model})`, 'success');
            } catch (error) {
                this.error = error.message;
                this.showNotification('エラー: ' + error.message, 'error');
            } finally {
                this.loading = false;
                this.aiGenerating = false;
                this.loadingMessage = '';
            }
        },

        // クリップボードにコピー
        async copyToClipboard(text) {
            if (!text) {
                this.showNotification('コピーする内容がありません', 'warning');
                return;
            }

            try {
                await navigator.clipboard.writeText(text);
                this.showNotification('クリップボードにコピーしました', 'success');
            } catch (error) {
                this.showNotification('コピーに失敗しました: ' + error.message, 'error');
            }
        },

        // 計算プロパティ

        get filteredItems() {
            return this.items.filter(item => {
                // 日付フィルタ（カレンダーで日付を選択している場合）
                if (this.selectedDate) {
                    if (!item.posted_at_history || item.posted_at_history.length === 0) {
                        return false;
                    }
                    const postedDate = new Date(item.posted_at_history[0]);
                    const postedDateStr = postedDate.getFullYear() + '-' +
                        String(postedDate.getMonth() + 1).padStart(2, '0') + '-' +
                        String(postedDate.getDate()).padStart(2, '0');

                    if (postedDateStr !== this.selectedDate) {
                        return false;
                    }
                }

                // 検索フィルタ
                if (this.searchQuery && !item.name.toLowerCase().includes(this.searchQuery.toLowerCase())) {
                    return false;
                }

                // ハッシュタグフィルタ
                if (this.hashtagQuery) {
                    const query = this.hashtagQuery.toLowerCase().trim();
                    const description = (item.description || '').toLowerCase();
                    // #を含む場合と含まない場合の両方に対応
                    const searchTag = query.startsWith('#') ? query : '#' + query;

                    if (!description.includes(searchTag)) {
                        return false;
                    }
                }

                // 状態フィルタ
                if (this.statusFilter !== '全て' && item.status !== this.statusFilter) {
                    return false;
                }

                // 優先度フィルタ
                if (this.priorityFilter !== '全て' && item.priority != this.priorityFilter) {
                    return false;
                }

                return true;
            }).sort((a, b) => {
                // 優先度が高い順、更新日時が新しい順
                if (a.priority !== b.priority) {
                    return b.priority - a.priority;
                }
                return new Date(b.updated_at) - new Date(a.updated_at);
            });
        },

        // 未投稿の商品数
        get unpublishedCount() {
            return this.items.filter(item => item.status === '未投稿').length;
        },

        // 今週投稿した商品数
        get weekPostedCount() {
            const oneWeekAgo = new Date();
            oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

            return this.items.filter(item => {
                if (!item.posted_at_history || item.posted_at_history.length === 0) return false;
                return new Date(item.posted_at_history[0]) >= oneWeekAgo;
            }).length;
        },

        // カレンダー表示用のメソッド

        // カレンダーの日付配列を生成
        get calendarDays() {
            const year = this.calendarYear;
            const month = this.calendarMonth;

            // 月の初日
            const firstDay = new Date(year, month - 1, 1);
            const firstDayOfWeek = firstDay.getDay(); // 0=日曜

            // 月の最終日
            const lastDay = new Date(year, month, 0);
            const lastDate = lastDay.getDate();

            const days = [];

            // 前月の日付で埋める
            for (let i = 0; i < firstDayOfWeek; i++) {
                days.push({ date: null, isCurrentMonth: false });
            }

            // 当月の日付
            for (let date = 1; date <= lastDate; date++) {
                const dateStr = year + '-' +
                    String(month).padStart(2, '0') + '-' +
                    String(date).padStart(2, '0');

                days.push({
                    date: date,
                    dateStr: dateStr,
                    isCurrentMonth: true,
                    postedCount: this.getPostedCountByDate(dateStr)
                });
            }

            return days;
        },

        // 指定日の投稿数を取得
        getPostedCountByDate(dateStr) {
            return this.items.filter(item => {
                if (!item.posted_at_history || item.posted_at_history.length === 0) return false;
                const postedDate = new Date(item.posted_at_history[0]);
                const postedDateStr = postedDate.getFullYear() + '-' +
                    String(postedDate.getMonth() + 1).padStart(2, '0') + '-' +
                    String(postedDate.getDate()).padStart(2, '0');
                return postedDateStr === dateStr;
            }).length;
        },

        // 前月に移動
        previousMonth() {
            if (this.calendarMonth === 1) {
                this.calendarMonth = 12;
                this.calendarYear--;
            } else {
                this.calendarMonth--;
            }
        },

        // 次月に移動
        nextMonth() {
            if (this.calendarMonth === 12) {
                this.calendarMonth = 1;
                this.calendarYear++;
            } else {
                this.calendarMonth++;
            }
        },

        // 今月に戻る
        goToToday() {
            const today = new Date();
            this.calendarYear = today.getFullYear();
            this.calendarMonth = today.getMonth() + 1;
        },

        // カレンダーの日付を選択して商品一覧にフィルタリング表示
        selectCalendarDate(dateStr) {
            if (!dateStr) return;

            const count = this.getPostedCountByDate(dateStr);
            if (count === 0) return;

            this.selectedDate = dateStr;
            this.changeViewMode('grid');
            this.statusFilter = '投稿済み';
        },

        // 日付フィルタをクリア
        clearDateFilter() {
            this.selectedDate = null;
        },

        // ルーティング関連メソッド

        // currentView + viewMode -> URLハッシュに変換
        viewToHash(view, mode) {
            if (view === 'items' && mode) {
                return `#/items/${mode}`;
            }
            const viewMap = {
                'setup': '#/',
                'items': '#/items',
                'profile-basic': '#/profile/basic',
                'profile-ai': '#/profile/ai',
                'trash': '#/trash'
            };
            return viewMap[view] || '#/';
        },

        // URLハッシュ -> currentView + viewModeに変換
        hashToView(hash) {
            if (hash.startsWith('#/items/')) {
                const mode = hash.replace('#/items/', '');
                if (['grid', 'list', 'compact', 'calendar'].includes(mode)) {
                    return { view: 'items', mode: mode };
                }
            }

            const hashMap = {
                '#/': 'setup',
                '#/items': 'items',
                '#/profile/basic': 'profile-basic',
                '#/profile/ai': 'profile-ai',
                '#/trash': 'trash'
            };
            const view = hashMap[hash] || (hash === '' ? 'setup' : null);
            return view ? { view: view, mode: null } : null;
        },

        // 画面遷移（currentView変更 + URL更新）
        navigateTo(view, mode = null) {
            this.currentView = view;
            const hash = this.viewToHash(view, mode);
            if (window.location.hash !== hash) {
                window.location.hash = hash;
            }

            // ページのスクロール位置を一番上にリセット
            this.$nextTick(() => {
                window.scrollTo(0, 0);
            });
        },

        // 表示モード変更（viewMode変更 + URL更新）
        changeViewMode(mode) {
            this.viewMode = mode;
            if (this.currentView === 'items') {
                const hash = this.viewToHash('items', mode);
                if (window.location.hash !== hash) {
                    window.location.hash = hash;
                }
            }
        },

        // URLから画面状態を復元
        syncFromURL() {
            const hash = window.location.hash;
            const result = this.hashToView(hash);
            if (result) {
                if (this.currentView !== result.view) {
                    this.currentView = result.view;
                }
                if (result.mode && this.viewMode !== result.mode) {
                    this.viewMode = result.mode;
                }
            }
        }
    };
}
