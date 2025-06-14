import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Space,
  Card,
  Input,
  Form,
  Toast,
  NavBar,
  Loading,
  Modal,
  TextArea,
  Divider
} from 'antd-mobile';
import {
  CameraOutline,
  PictureOutline,
  CheckOutline,
  CloseOutline,
  EditSOutline,
  ScanningOutline,
  LoopOutline
} from 'antd-mobile-icons';
import axios from 'axios';
import { getCameraManager } from '../utils/cameraManager';
import { getDeviceType } from '../utils/deviceDetector';
import MobileCameraModal from '../components/MobileCameraModal';

const ScanUploadPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [parseLoading, setParseLoading] = useState(false);

  // 圖片管理狀態
  const [frontImage, setFrontImage] = useState({
    file: null,
    preview: null,
    ocrText: '',
    parseStatus: null // 'success', 'error', 'parsing', null
  });
  const [backImage, setBackImage] = useState({
    file: null,
    preview: null,
    ocrText: '',
    parseStatus: null // 'success', 'error', 'parsing', null
  });
  const [cameraModalVisible, setCameraModalVisible] = useState(false);
  const [currentCaptureTarget, setCurrentCaptureTarget] = useState('front'); // 'front' | 'back'
  const [stream, setStream] = useState(null);

  // 新增：相機管理器和設備類型狀態
  const [cameraManager, setCameraManager] = useState(null);
  const [isMobileCameraMode, setIsMobileCameraMode] = useState(false);
  
  // 統一的名片資料狀態 - 完整22個欄位系統
  const [cardData, setCardData] = useState({
    // 基本資訊（中英文）
    name: '',                    // 姓名
    name_en: '',                 // 英文姓名
    company_name: '',            // 公司名稱
    company_name_en: '',         // 英文公司名稱
    position: '',                // 職位
    position_en: '',             // 英文職位
    
    // 部門組織架構（中英文，三層）
    department1: '',             // 部門1(中文)
    department1_en: '',          // 部門1(英文)
    department2: '',             // 部門2(中文)
    department2_en: '',          // 部門2(英文)
    department3: '',             // 部門3(中文)
    department3_en: '',          // 部門3(英文)
    
    // 聯絡資訊
    mobile_phone: '',            // 手機
    company_phone1: '',          // 公司電話1
    company_phone2: '',          // 公司電話2
    email: '',                   // Email
    line_id: '',                 // Line ID
    
    // 地址資訊（中英文）
    company_address1: '',        // 公司地址一(中文)
    company_address1_en: '',     // 公司地址一(英文)
    company_address2: '',        // 公司地址二(中文)
    company_address2_en: '',     // 公司地址二(英文)
    
    // 備註資訊
    note1: '',                   // 備註1
    note2: ''                    // 備註2
  });
  
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // 初始化相機管理器和設備檢測
  useEffect(() => {
    const initializeCamera = async () => {
      try {
        const manager = getCameraManager();
        setCameraManager(manager);

        const type = getDeviceType();
        setIsMobileCameraMode(type === 'mobile' || type === 'tablet');

        console.log(`設備類型: ${type}, 移動端相機模式: ${type === 'mobile' || type === 'tablet'}`);
      } catch (error) {
        console.error('初始化相機管理器失敗:', error);
      }
    };

    initializeCamera();
  }, []);

  // 更新圖片解析狀態
  const updateImageParseStatus = useCallback((side, status) => {
    if (side === 'front') {
      setFrontImage(prev => ({ ...prev, parseStatus: status }));
    } else {
      setBackImage(prev => ({ ...prev, parseStatus: status }));
    }
  }, []);

  // 智能解析OCR文字並填充表單
  const parseAndFillOCRData = useCallback(async (ocrText, side) => {
    if (!ocrText) return;
    
    try {
      updateImageParseStatus(side, 'parsing');
      
      // 調用後端智能解析API
      const response = await axios.post('/api/v1/ocr/parse-fields', {
        ocr_text: ocrText,
        side: side
      });

      if (response.data.success) {
        const parsedFields = response.data.parsed_fields;
        
        // === 新增：中英文姓名自動分配 ===
        if (parsedFields.name && !parsedFields.name_en) {
          if (/^[A-Za-z .'-]+$/.test(parsedFields.name)) {
            parsedFields.name_en = parsedFields.name;
            parsedFields.name = '';
          } else if (!/[\u4e00-\u9fff]/.test(parsedFields.name)) {
            // 若不含中文也不全為英文，仍歸為英文名
            parsedFields.name_en = parsedFields.name;
            parsedFields.name = '';
          }
        }
        if (parsedFields.name_en && !parsedFields.name) {
          if (/[\u4e00-\u9fff]/.test(parsedFields.name_en)) {
            parsedFields.name = parsedFields.name_en;
            parsedFields.name_en = '';
          }
        }
        // === END ===
        
        // === 新增：公司名稱與職位中英文自動分配 ===
        // 公司名稱
        if (parsedFields.company_name && !parsedFields.company_name_en) {
          if (/^[A-Za-z0-9 .,'&()-]+$/.test(parsedFields.company_name)) {
            parsedFields.company_name_en = parsedFields.company_name;
            parsedFields.company_name = '';
          } else if (!/[\u4e00-\u9fff]/.test(parsedFields.company_name)) {
            parsedFields.company_name_en = parsedFields.company_name;
            parsedFields.company_name = '';
          }
        }
        if (parsedFields.company_name_en && !parsedFields.company_name) {
          if (/[\u4e00-\u9fff]/.test(parsedFields.company_name_en)) {
            parsedFields.company_name = parsedFields.company_name_en;
            parsedFields.company_name_en = '';
          }
        }
        // 職位
        if (parsedFields.position && !parsedFields.position_en) {
          if (/^[A-Za-z0-9 .,'&()-]+$/.test(parsedFields.position)) {
            parsedFields.position_en = parsedFields.position;
            parsedFields.position = '';
          } else if (!/[\u4e00-\u9fff]/.test(parsedFields.position)) {
            parsedFields.position_en = parsedFields.position;
            parsedFields.position = '';
          }
        }
        if (parsedFields.position_en && !parsedFields.position) {
          if (/[\u4e00-\u9fff]/.test(parsedFields.position_en)) {
            parsedFields.position = parsedFields.position_en;
            parsedFields.position_en = '';
          }
        }
        // === END ===
        
        // === 新增：部門與公司地址中英文自動分配 ===
        // 部門
        for (let i = 1; i <= 3; i++) {
          const zhKey = `department${i}`;
          const enKey = `department${i}_en`;
          if (parsedFields[zhKey] && !parsedFields[enKey]) {
            if (/^[A-Za-z0-9 .,'&()-]+$/.test(parsedFields[zhKey])) {
              parsedFields[enKey] = parsedFields[zhKey];
              parsedFields[zhKey] = '';
            } else if (!/[\u4e00-\u9fff]/.test(parsedFields[zhKey])) {
              parsedFields[enKey] = parsedFields[zhKey];
              parsedFields[zhKey] = '';
            }
          }
          if (parsedFields[enKey] && !parsedFields[zhKey]) {
            if (/[\u4e00-\u9fff]/.test(parsedFields[enKey])) {
              parsedFields[zhKey] = parsedFields[enKey];
              parsedFields[enKey] = '';
            }
          }
        }
        // 公司地址
        for (let i = 1; i <= 2; i++) {
          const zhKey = `company_address${i}`;
          const enKey = `company_address${i}_en`;
          if (parsedFields[zhKey] && !parsedFields[enKey]) {
            if (/^[A-Za-z0-9 .,'&()-]+$/.test(parsedFields[zhKey])) {
              parsedFields[enKey] = parsedFields[zhKey];
              parsedFields[zhKey] = '';
            } else if (!/[\u4e00-\u9fff]/.test(parsedFields[zhKey])) {
              parsedFields[enKey] = parsedFields[zhKey];
              parsedFields[zhKey] = '';
            }
          }
          if (parsedFields[enKey] && !parsedFields[zhKey]) {
            if (/[\u4e00-\u9fff]/.test(parsedFields[enKey])) {
              parsedFields[zhKey] = parsedFields[enKey];
              parsedFields[enKey] = '';
            }
          }
        }
        // === END ===
        
        setCardData(prevData => {
          const updatedData = { ...prevData };
          Object.keys(parsedFields).forEach(field => {
            if (parsedFields[field] && (!updatedData[field] || updatedData[field].trim() === '')) {
              updatedData[field] = parsedFields[field];
            }
          });
          return updatedData;
        });
        
        updateImageParseStatus(side, 'success');
        
        Toast.show({
          content: `${side === 'front' ? '正面' : '反面'}資料解析完成！已自動填入相關欄位`,
          position: 'center',
        });
      } else {
        updateImageParseStatus(side, 'error');
        Toast.show({
          content: 'OCR資料解析失敗，請手動編輯',
          position: 'center',
        });
      }
    } catch (error) {
      console.error('OCR解析錯誤:', error);
      updateImageParseStatus(side, 'error');
      Toast.show({
        content: 'OCR資料解析失敗，請檢查網絡連接',
        position: 'center',
      });
    }
  }, [updateImageParseStatus]);

  // 執行OCR並智能解析
  const performOCR = useCallback(async (file, side) => {
    if (!file) return;
    
    setLoading(true);
    updateImageParseStatus(side, 'parsing');
    
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('/api/v1/ocr/image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        const ocrText = response.data.text;
        
        // 更新對應面的OCR結果
        if (side === 'front') {
          setFrontImage(prev => ({ ...prev, ocrText }));
        } else {
          setBackImage(prev => ({ ...prev, ocrText }));
        }
        
        // 執行智能解析並填充表單
        await parseAndFillOCRData(ocrText, side);
        
        Toast.show({
          content: `${side === 'front' ? '正面' : '反面'}OCR識別完成！`,
          position: 'center',
        });
      } else {
        updateImageParseStatus(side, 'error');
        Toast.show({
          content: 'OCR識別失敗，請重試',
          position: 'center',
        });
      }
    } catch (error) {
      console.error('OCR錯誤:', error);
      updateImageParseStatus(side, 'error');
      Toast.show({
        content: 'OCR識別失敗，請檢查網絡連接並重試',
        position: 'center',
      });
    } finally {
      setLoading(false);
    }
  }, [parseAndFillOCRData, updateImageParseStatus]);

  // 手動解析當前圖片
  const handleManualParse = useCallback(async () => {
    const currentImage = currentCaptureTarget === 'front' ? frontImage : backImage;
    
    if (!currentImage.file) {
      Toast.show({
        content: '請先拍攝或選擇圖片',
        position: 'center',
      });
      return;
    }

    if (currentImage.ocrText) {
      // 如果已有OCR文本，直接解析
      setParseLoading(true);
      try {
        await parseAndFillOCRData(currentImage.ocrText, currentCaptureTarget);
      } finally {
        setParseLoading(false);
      }
    } else {
      // 如果沒有OCR文本，執行完整的OCR流程
      await performOCR(currentImage.file, currentCaptureTarget);
    }
  }, [currentCaptureTarget, frontImage, backImage, parseAndFillOCRData, performOCR]);

  // 處理圖片上傳
  const handleImageUpload = useCallback(async (file, target = currentCaptureTarget) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      if (target === 'front') {
        setFrontImage(prev => ({ 
          ...prev, 
          file, 
          preview: e.target.result,
          parseStatus: null // 重置解析狀態
        }));
      } else {
        setBackImage(prev => ({ 
          ...prev, 
          file, 
          preview: e.target.result,
          parseStatus: null // 重置解析狀態
        }));
      }
    };
    reader.readAsDataURL(file);

    // 自動執行OCR
    await performOCR(file, target);
  }, [performOCR, currentCaptureTarget]);

  // 啟動攝像頭 - 使用新的相機管理器
  const startCamera = async (target) => {
    if (!cameraManager) {
      Toast.show({
        content: '相機管理器未初始化',
        position: 'center',
      });
      return;
    }

    setCurrentCaptureTarget(target);

    try {
      if (isMobileCameraMode) {
        // 移動端：使用全屏相機模式
        setCameraModalVisible(true);
      } else {
        // Web端：使用傳統Modal模式
        setCameraModalVisible(true);

        // 等待Modal渲染完成後啟動相機
        setTimeout(async () => {
          try {
            const mediaStream = await cameraManager.startCamera(target, {
              videoElement: videoRef.current,
              canvasElement: canvasRef.current
            });
            setStream(mediaStream);

            console.log('Web端相機啟動成功', {
              target,
              videoElement: !!videoRef.current,
              canvasElement: !!canvasRef.current
            });
          } catch (error) {
            console.error('Web端相機啟動失敗:', error);
            setCameraModalVisible(false);
            throw error;
          }
        }, 100);
      }
    } catch (error) {
      console.error('無法啟動攝像頭:', error);
      Toast.show({
        content: '無法啟動攝像頭，請檢查權限設置',
        position: 'center',
      });
    }
  };

  // 停止攝像頭 - 使用新的相機管理器
  const stopCamera = () => {
    if (cameraManager) {
      cameraManager.stopCamera();
    }
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setCameraModalVisible(false);
  };

  // 拍照 - 使用新的相機管理器
  const takePhoto = async () => {
    if (!cameraManager) {
      Toast.show({
        content: '相機管理器未初始化',
        position: 'center',
      });
      return;
    }

    // 檢查相機狀態
    const status = cameraManager.getStatus();
    if (!status.isInitialized || !status.strategy || !status.strategy.isActive) {
      Toast.show({
        content: '相機未準備就緒，請重新啟動相機',
        position: 'center',
      });
      return;
    }

    try {
      console.log('開始拍照...', { target: currentCaptureTarget, mode: status.mode });

      const result = await cameraManager.takePhoto();

      if (result && result.file) {
        console.log('拍照成功，開始處理圖片...', {
          fileSize: result.file.size,
          fileName: result.file.name
        });

        await handleImageUpload(result.file, currentCaptureTarget);
        stopCamera();

        Toast.show({
          content: '拍照成功！',
          position: 'center',
        });
      } else {
        throw new Error('拍照結果無效');
      }
    } catch (error) {
      console.error('拍照失敗:', error);
      Toast.show({
        content: `拍照失敗：${error.message || '請重試'}`,
        position: 'center',
      });
    }
  };

  // 移動端相機拍照完成回調
  const handleMobilePhotoTaken = async (data) => {
    if (data && data.file) {
      await handleImageUpload(data.file, currentCaptureTarget);
    }
  };

  // 從相冊選擇
  const selectFromGallery = (target) => {
    setCurrentCaptureTarget(target);
    fileInputRef.current?.click();
  };

  // 處理文件選擇
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      handleImageUpload(file, currentCaptureTarget);
      // 清空input以便重複選擇同一文件
      event.target.value = '';
    }
  };

  // 保存名片資料
  const handleSave = async () => {
    // 驗證必填欄位
    if (!cardData.name.trim()) {
      Toast.show({
        content: '請輸入姓名',
        position: 'center',
      });
      return;
    }

    setLoading(true);
    try {
      const saveData = new FormData();
      
      // 添加名片資料
      Object.keys(cardData).forEach(key => {
        if (cardData[key]) {
          saveData.append(key, cardData[key]);
        }
      });
      
      // 添加圖片文件
      if (frontImage.file) {
        saveData.append('front_image', frontImage.file);
      }
      if (backImage.file) {
        saveData.append('back_image', backImage.file);
      }
      
      // 添加OCR原始文字
      if (frontImage.ocrText) {
        saveData.append('front_ocr_text', frontImage.ocrText);
      }
      if (backImage.ocrText) {
        saveData.append('back_ocr_text', backImage.ocrText);
      }

      const response = await axios.post('/api/v1/cards/', saveData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data) {
        Toast.show({
          content: '名片保存成功！',
          position: 'center',
        });
        // 清空表單
        setCardData({
          name: '',
          company_name: '',
          position: '',
          mobile_phone: '',
          office_phone: '',
          email: '',
          line_id: '',
          notes: '',
          company_address_1: '',
          company_address_2: ''
        });
        setFrontImage({ file: null, preview: null, ocrText: '', parseStatus: null });
        setBackImage({ file: null, preview: null, ocrText: '', parseStatus: null });
        // 導航到名片管理頁面
        navigate('/cards');
      }
    } catch (error) {
      console.error('保存失敗:', error);
      Toast.show({
        content: '保存失敗，請重試',
        position: 'center',
      });
    } finally {
      setLoading(false);
    }
  };

  // 表單欄位更新處理
  const handleFieldChange = (field, value) => {
    setCardData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // 獲取解析狀態圖標和顏色
  const getParseStatusIcon = (status) => {
    switch (status) {
      case 'parsing':
        return <LoopOutline style={{ color: '#1677ff', animation: 'spin 1s linear infinite' }} />;
      case 'success':
        return <CheckOutline style={{ color: '#52c41a' }} />;
      case 'error':
        return <CloseOutline style={{ color: '#ff4d4f' }} />;
      default:
        return null;
    }
  };

  // 添加旋轉動畫樣式
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  return (
    <div className="scan-upload-page">
      <NavBar onBack={() => navigate(-1)}>名片資料輸入</NavBar>
      
      {loading && <Loading />}
      
      <div className="content" style={{ padding: '16px' }}>
        {/* 圖片拍攝區域 */}
        <Card title="拍攝名片" style={{ marginBottom: '16px' }}>
          <div className="image-capture-section">
            {/* 拍攝模式切換與解析操作 */}
            <div className="capture-mode-switch" style={{ marginBottom: '16px' }}>
              <Space style={{ width: '100%', justifyContent: 'center', gap: '8px' }}>
                <Button 
                  color={currentCaptureTarget === 'front' ? 'primary' : 'default'}
                  fill={currentCaptureTarget === 'front' ? 'solid' : 'outline'}
                  onClick={() => setCurrentCaptureTarget('front')}
                  style={{ flex: 1 }}
                >
                  正面
                </Button>
                <Button 
                  color={currentCaptureTarget === 'back' ? 'primary' : 'default'}
                  fill={currentCaptureTarget === 'back' ? 'solid' : 'outline'}
                  onClick={() => setCurrentCaptureTarget('back')}
                  style={{ flex: 1 }}
                >
                  反面
                </Button>
                <Button 
                  color="success" 
                  fill="outline"
                  onClick={handleManualParse}
                  disabled={(currentCaptureTarget === 'front' ? !frontImage.file : !backImage.file) || parseLoading}
                  style={{ flex: 1 }}
                >
                  {parseLoading ? <LoopOutline style={{ animation: 'spin 1s linear infinite' }} /> : <ScanningOutline />} 解析
                </Button>
              </Space>
            </div>

            {/* 單一拍攝框 */}
            <div className="single-capture-frame">
              <div className="current-side-title" style={{ marginBottom: '8px', fontSize: '14px', fontWeight: 'bold', textAlign: 'center' }}>
                當前拍攝: {currentCaptureTarget === 'front' ? '正面' : '反面'}
                {/* 解析狀態指示 */}
                {getParseStatusIcon((currentCaptureTarget === 'front' ? frontImage : backImage).parseStatus)}
              </div>
              
              {/* 顯示當前選中面的圖片 */}
              {(currentCaptureTarget === 'front' ? frontImage.preview : backImage.preview) ? (
                <img
                  src={currentCaptureTarget === 'front' ? frontImage.preview : backImage.preview}
                  alt={`名片${currentCaptureTarget === 'front' ? '正面' : '反面'}`}
                  style={{
                    width: '100%',
                    height: 'clamp(280px, 40vw, 400px)',
                    objectFit: 'cover',
                    borderRadius: '8px',
                    marginBottom: '16px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                    transition: 'all 0.3s ease'
                  }}
                />
              ) : (
                <div
                  style={{
                    width: '100%',
                    height: 'clamp(280px, 40vw, 400px)',
                    border: '2px dashed #d9d9d9',
                    borderRadius: '8px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#999',
                    marginBottom: '16px',
                    background: '#fafafa',
                    transition: 'all 0.3s ease'
                  }}
                >
                  <CameraOutline style={{ fontSize: '64px', marginBottom: '12px', color: '#ccc' }} />
                  <div style={{ fontSize: '16px', textAlign: 'center' }}>
                    請拍攝名片{currentCaptureTarget === 'front' ? '正面' : '反面'}
                  </div>
                  <div style={{ fontSize: '14px', color: '#bbb', marginTop: '8px' }}>
                    點擊下方按鈕開始拍照
                  </div>
                </div>
              )}

              {/* 拍攝操作按鈕 */}
              <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                <Button 
                  color="primary" 
                  onClick={() => startCamera(currentCaptureTarget)}
                  style={{ flex: 1 }}
                >
                  <CameraOutline /> 拍照
                </Button>
                <Button 
                  color="primary" 
                  fill="outline"
                  onClick={() => selectFromGallery(currentCaptureTarget)}
                  style={{ flex: 1 }}
                >
                  <PictureOutline /> 相冊
                </Button>
              </div>

              {/* 拍攝狀態指示 */}
              <div className="capture-status" style={{ marginTop: '12px', textAlign: 'center' }}>
                <Space>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <div style={{ 
                      width: '8px', 
                      height: '8px', 
                      borderRadius: '50%', 
                      backgroundColor: frontImage.preview ? '#52c41a' : '#d9d9d9' 
                    }}></div>
                    <span style={{ fontSize: '12px', color: frontImage.preview ? '#52c41a' : '#8c8c8c' }}>
                      正面 {frontImage.preview ? '已拍攝' : '未拍攝'}
                    </span>
                    {frontImage.parseStatus && getParseStatusIcon(frontImage.parseStatus)}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <div style={{ 
                      width: '8px', 
                      height: '8px', 
                      borderRadius: '50%', 
                      backgroundColor: backImage.preview ? '#52c41a' : '#d9d9d9' 
                    }}></div>
                    <span style={{ fontSize: '12px', color: backImage.preview ? '#52c41a' : '#8c8c8c' }}>
                      反面 {backImage.preview ? '已拍攝' : '未拍攝'}
                    </span>
                    {backImage.parseStatus && getParseStatusIcon(backImage.parseStatus)}
                  </div>
                </Space>
              </div>
            </div>
          </div>
        </Card>

        {/* 統一的名片資料編輯表單 */}
        <Card title="名片資料" extra={<EditSOutline />} style={{ marginBottom: '16px' }}>
          <Form layout="vertical">
            {/* 基本資訊（中英文） */}
            <div className="form-section">
              <Divider>基本資訊</Divider>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Form.Item label="姓名 *" required>
                  <Input
                    placeholder="請輸入中文姓名"
                    value={cardData.name}
                    onChange={(value) => handleFieldChange('name', value)}
                  />
                </Form.Item>
                
                <Form.Item label="英文姓名">
                  <Input
                    placeholder="English Name"
                    value={cardData.name_en}
                    onChange={(value) => handleFieldChange('name_en', value)}
                  />
                </Form.Item>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Form.Item label="公司名稱">
                  <Input
                    placeholder="請輸入公司名稱"
                    value={cardData.company_name}
                    onChange={(value) => handleFieldChange('company_name', value)}
                  />
                </Form.Item>
                
                <Form.Item label="英文公司名稱">
                  <Input
                    placeholder="Company Name"
                    value={cardData.company_name_en}
                    onChange={(value) => handleFieldChange('company_name_en', value)}
                  />
                </Form.Item>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Form.Item label="職位">
                  <Input
                    placeholder="請輸入職位"
                    value={cardData.position}
                    onChange={(value) => handleFieldChange('position', value)}
                  />
                </Form.Item>
                
                <Form.Item label="英文職位">
                  <Input
                    placeholder="Position"
                    value={cardData.position_en}
                    onChange={(value) => handleFieldChange('position_en', value)}
                  />
                </Form.Item>
              </div>
            </div>

            {/* 部門組織架構 */}
            <div className="form-section">
              <Divider>部門組織架構</Divider>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Form.Item label="部門1(單位1)">
                  <Input
                    placeholder="請輸入第一層部門"
                    value={cardData.department1}
                    onChange={(value) => handleFieldChange('department1', value)}
                  />
                </Form.Item>
                
                <Form.Item label="Department1">
                  <Input
                    placeholder="Department Level 1"
                    value={cardData.department1_en}
                    onChange={(value) => handleFieldChange('department1_en', value)}
                  />
                </Form.Item>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Form.Item label="部門2(單位2)">
                  <Input
                    placeholder="請輸入第二層部門"
                    value={cardData.department2}
                    onChange={(value) => handleFieldChange('department2', value)}
                  />
                </Form.Item>
                
                <Form.Item label="Department2">
                  <Input
                    placeholder="Department Level 2"
                    value={cardData.department2_en}
                    onChange={(value) => handleFieldChange('department2_en', value)}
                  />
                </Form.Item>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Form.Item label="部門3(單位3)">
                  <Input
                    placeholder="請輸入第三層部門"
                    value={cardData.department3}
                    onChange={(value) => handleFieldChange('department3', value)}
                  />
                </Form.Item>
                
                <Form.Item label="Department3">
                  <Input
                    placeholder="Department Level 3"
                    value={cardData.department3_en}
                    onChange={(value) => handleFieldChange('department3_en', value)}
                  />
                </Form.Item>
              </div>
            </div>

            {/* 聯絡資訊 */}
            <div className="form-section">
              <Divider>聯絡資訊</Divider>
              
              <Form.Item label="手機(mobile)">
                <Input
                  placeholder="請輸入手機號碼"
                  value={cardData.mobile_phone}
                  onChange={(value) => handleFieldChange('mobile_phone', value)}
                />
              </Form.Item>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Form.Item label="公司電話1">
                  <Input
                    placeholder="請輸入公司電話"
                    value={cardData.company_phone1}
                    onChange={(value) => handleFieldChange('company_phone1', value)}
                  />
                </Form.Item>
                
                <Form.Item label="公司電話2">
                  <Input
                    placeholder="請輸入第二組電話"
                    value={cardData.company_phone2}
                    onChange={(value) => handleFieldChange('company_phone2', value)}
                  />
                </Form.Item>
              </div>
              
              <Form.Item label="Email">
                <Input
                  placeholder="請輸入Email地址"
                  value={cardData.email}
                  onChange={(value) => handleFieldChange('email', value)}
                />
              </Form.Item>
              
              <Form.Item label="Line ID">
                <Input
                  placeholder="請輸入Line ID"
                  value={cardData.line_id}
                  onChange={(value) => handleFieldChange('line_id', value)}
                />
              </Form.Item>
            </div>

            {/* 地址資訊（中英文） */}
            <div className="form-section">
              <Divider>地址資訊</Divider>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Form.Item label="公司地址一">
                  <Input
                    placeholder="請輸入公司地址"
                    value={cardData.company_address1}
                    onChange={(value) => handleFieldChange('company_address1', value)}
                  />
                </Form.Item>
                
                <Form.Item label="Company Address1(EN)">
                  <Input
                    placeholder="Company Address 1"
                    value={cardData.company_address1_en}
                    onChange={(value) => handleFieldChange('company_address1_en', value)}
                  />
                </Form.Item>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Form.Item label="公司地址二">
                  <Input
                    placeholder="請輸入公司地址（補充）"
                    value={cardData.company_address2}
                    onChange={(value) => handleFieldChange('company_address2', value)}
                  />
                </Form.Item>
                
                <Form.Item label="Company Address2(EN)">
                  <Input
                    placeholder="Company Address 2"
                    value={cardData.company_address2_en}
                    onChange={(value) => handleFieldChange('company_address2_en', value)}
                  />
                </Form.Item>
              </div>
            </div>

            {/* 備註資訊 */}
            <div className="form-section">
              <Divider>備註資訊</Divider>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <Form.Item label="備註1(note1)">
                  <TextArea
                    placeholder="請輸入備註資訊"
                    rows={3}
                    value={cardData.note1}
                    onChange={(value) => handleFieldChange('note1', value)}
                  />
                </Form.Item>
                
                <Form.Item label="備註2(note2)">
                  <TextArea
                    placeholder="請輸入額外備註"
                    rows={3}
                    value={cardData.note2}
                    onChange={(value) => handleFieldChange('note2', value)}
                  />
                </Form.Item>
              </div>
            </div>
          </Form>
        </Card>

        {/* 操作按鈕 */}
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button 
            color="primary" 
            size="large" 
            block 
            onClick={handleSave}
            disabled={loading}
          >
            <CheckOutline /> 保存名片
          </Button>
        </Space>
      </div>

      {/* 相機模態框 - 根據設備類型選擇不同的實現 */}
      {isMobileCameraMode ? (
        // 移動端：使用全屏相機組件
        <MobileCameraModal
          visible={cameraModalVisible}
          onClose={stopCamera}
          onPhotoTaken={handleMobilePhotoTaken}
          cameraManager={cameraManager}
          target={currentCaptureTarget}
        />
      ) : (
        // Web端：使用傳統Modal
        <Modal
          visible={cameraModalVisible}
          content={
            <div className="camera-modal">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                style={{
                  width: '100%',
                  height: 'clamp(350px, 50vh, 500px)',
                  objectFit: 'cover',
                  borderRadius: '8px',
                  background: '#000'
                }}
              />
              <canvas ref={canvasRef} style={{ display: 'none' }} />
              <div style={{ marginTop: '20px', textAlign: 'center' }}>
                <Space size="large">
                  <Button
                    color="primary"
                    size="large"
                    onClick={takePhoto}
                    style={{ minWidth: '100px' }}
                  >
                    <CameraOutline /> 拍照
                  </Button>
                  <Button
                    color="default"
                    size="large"
                    onClick={stopCamera}
                    style={{ minWidth: '100px' }}
                  >
                    <CloseOutline /> 取消
                  </Button>
                </Space>
              </div>
            </div>
          }
          onClose={stopCamera}
        />
      )}

      {/* 隱藏的文件選擇輸入 */}
      <input
        type="file"
        ref={fileInputRef}
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleFileSelect}
      />
    </div>
  );
};

export default ScanUploadPage; 