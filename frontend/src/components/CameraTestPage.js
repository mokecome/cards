/**
 * 相機系統測試頁面
 * 用於測試新的環境自適應相機功能
 */

import React, { useState, useEffect } from 'react';
import { Button, Card, Space, Toast } from 'antd-mobile';
import { CameraOutline, CheckOutline } from 'antd-mobile-icons';
import { getCameraManager } from '../utils/cameraManager';
import { getEnvironmentInfo } from '../utils/deviceDetector';
import MobileCameraModal from './MobileCameraModal';

const CameraTestPage = () => {
  const [cameraManager, setCameraManager] = useState(null);
  const [deviceInfo, setDeviceInfo] = useState(null);
  const [cameraStatus, setCameraStatus] = useState('未初始化');
  const [showMobileCamera, setShowMobileCamera] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [isMobile, setIsMobile] = useState(false);

  // 初始化
  useEffect(() => {
    const initializeSystem = async () => {
      try {
        // 獲取設備信息
        const envInfo = await getEnvironmentInfo();
        setDeviceInfo(envInfo);
        setIsMobile(envInfo.deviceType === 'mobile' || envInfo.deviceType === 'tablet');
        
        // 初始化相機管理器
        const manager = getCameraManager();
        setCameraManager(manager);
        
        setCameraStatus('已初始化');
        
        console.log('設備信息:', envInfo);
        console.log('相機管理器:', manager);
        
      } catch (error) {
        console.error('初始化失敗:', error);
        setCameraStatus('初始化失敗');
        Toast.show({
          content: '系統初始化失敗',
          position: 'center'
        });
      }
    };
    
    initializeSystem();
  }, []);

  // 測試相機啟動
  const handleTestCamera = async () => {
    if (!cameraManager) {
      Toast.show({
        content: '相機管理器未初始化',
        position: 'center'
      });
      return;
    }

    try {
      setCameraStatus('正在啟動相機...');
      
      if (isMobile) {
        // 移動端：使用全屏相機
        setShowMobileCamera(true);
      } else {
        // Web端：直接啟動相機
        await cameraManager.startCamera('back');
        setCameraStatus('相機已啟動 (Web模式)');
        
        Toast.show({
          content: '相機啟動成功！',
          position: 'center'
        });
      }
    } catch (error) {
      console.error('相機啟動失敗:', error);
      setCameraStatus('相機啟動失敗');
      Toast.show({
        content: '相機啟動失敗，請檢查權限',
        position: 'center'
      });
    }
  };

  // 測試拍照
  const handleTestPhoto = async () => {
    if (!cameraManager) return;

    try {
      setCameraStatus('正在拍照...');
      const result = await cameraManager.takePhoto();
      
      if (result && result.file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          setCapturedImage(e.target.result);
        };
        reader.readAsDataURL(result.file);
        
        setCameraStatus('拍照成功');
        Toast.show({
          content: '拍照成功！',
          position: 'center'
        });
      }
    } catch (error) {
      console.error('拍照失敗:', error);
      setCameraStatus('拍照失敗');
      Toast.show({
        content: '拍照失敗，請重試',
        position: 'center'
      });
    }
  };

  // 停止相機
  const handleStopCamera = () => {
    if (cameraManager) {
      cameraManager.stopCamera();
      setCameraStatus('相機已停止');
    }
  };

  // 移動端拍照完成回調
  const handleMobilePhotoTaken = (data) => {
    if (data && data.file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setCapturedImage(e.target.result);
      };
      reader.readAsDataURL(data.file);
      
      setCameraStatus('拍照成功 (移動端模式)');
      Toast.show({
        content: '拍照成功！',
        position: 'center'
      });
    }
    setShowMobileCamera(false);
  };

  // 關閉移動端相機
  const handleCloseMobileCamera = () => {
    setShowMobileCamera(false);
    setCameraStatus('相機已關閉');
  };



  return (
    <div style={{ padding: '16px', minHeight: '100vh', background: '#f5f5f5' }}>
      <Card title="相機系統測試" style={{ marginBottom: '16px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <strong>狀態：</strong> {cameraStatus}
          </div>
          
          {deviceInfo && (
            <div>
              <strong>設備類型：</strong> {deviceInfo.deviceType}
              <br />
              <strong>相機模式：</strong> {isMobile ? '移動端全屏' : 'Web端Modal'}
              <br />
              <strong>相機支持：</strong> {deviceInfo.camera.hasCamera ? '是' : '否'}
              <br />
              <strong>可用相機數量：</strong> {deviceInfo.camera.availableCameras.length}
            </div>
          )}
        </Space>
      </Card>

      <Card title="相機控制" style={{ marginBottom: '16px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button 
            color="primary" 
            size="large" 
            block 
            onClick={handleTestCamera}
            disabled={!cameraManager}
          >
            <CameraOutline /> 啟動相機
          </Button>
          
          {!isMobile && (
            <>
              <Button 
                color="primary" 
                size="large" 
                block 
                onClick={handleTestPhoto}
                disabled={!cameraManager || cameraStatus !== '相機已啟動 (Web模式)'}
              >
                <CheckOutline /> 拍照
              </Button>
              
              <Button 
                color="default" 
                size="large" 
                block 
                onClick={handleStopCamera}
                disabled={!cameraManager}
              >
                停止相機
              </Button>
            </>
          )}

        </Space>
      </Card>

      {capturedImage && (
        <Card title="拍攝結果" style={{ marginBottom: '16px' }}>
          <img
            src={capturedImage}
            alt="拍攝的照片"
            style={{
              width: '100%',
              height: '350px',
              objectFit: 'cover',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
            }}
          />
        </Card>
      )}

      {deviceInfo && (
        <Card title="詳細設備信息">
          <pre style={{ 
            fontSize: '12px', 
            background: '#f0f0f0', 
            padding: '8px', 
            borderRadius: '4px',
            overflow: 'auto'
          }}>
            {JSON.stringify(deviceInfo, null, 2)}
          </pre>
        </Card>
      )}

      {/* 移動端全屏相機 */}
      {isMobile && (
        <MobileCameraModal
          visible={showMobileCamera}
          onClose={handleCloseMobileCamera}
          onPhotoTaken={handleMobilePhotoTaken}
          cameraManager={cameraManager}
          target="back"
        />
      )}
    </div>
  );
};

export default CameraTestPage;
