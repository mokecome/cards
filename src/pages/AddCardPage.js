import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Card, 
  Button, 
  Space, 
  Toast, 
  NavBar,
  Form,
  Input,
  TextArea,
  Divider
} from 'antd-mobile';
import { CheckOutline, UserContactOutline } from 'antd-mobile-icons';
import axios from 'axios';

const AddCardPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  
  // 統一的名片資料狀態 - 與OCR掃描頁面保持一致的9個欄位
  const [cardData, setCardData] = useState({
    name: '',                    // 姓名
    company_name: '',            // 公司名稱
    position: '',                // 職位
    mobile_phone: '',            // 手機
    office_phone: '',            // 公司電話
    email: '',                   // Email
    line_id: '',                 // Line ID
    notes: '',                   // 備註
    company_address_1: '',       // 公司地址一
    company_address_2: ''        // 公司地址二
  });

  // 表單欄位更新處理
  const handleFieldChange = (field, value) => {
    setCardData(prev => ({
      ...prev,
      [field]: value
    }));
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

      const response = await axios.post('/api/v1/cards/', saveData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data) {
        Toast.show({
          content: '名片新增成功！',
          position: 'center',
        });
        // 導航到名片管理頁面
        navigate('/cards');
      }
    } catch (error) {
      console.error('保存失敗:', error);
      Toast.show({
        content: error.response?.data?.detail || '保存失敗，請重試',
        position: 'center',
      });
    } finally {
      setLoading(false);
    }
  };

  // 重置表單
  const handleReset = () => {
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
    Toast.show({
      content: '表單已重置',
      position: 'center',
    });
  };

  return (
    <div className="add-card-page">
      <NavBar onBack={() => navigate('/cards')}>手動新增名片</NavBar>
      
      <div className="content" style={{ padding: '16px' }}>
        {/* 名片資料編輯表單 */}
        <Card title="名片資料" extra={<UserContactOutline />} style={{ marginBottom: '16px' }}>
          <Form layout="vertical">
            {/* 基本資訊 */}
            <div className="form-section">
              <Divider>基本資訊</Divider>
              
              <Form.Item label="姓名 *" required>
                <Input
                  placeholder="請輸入姓名"
                  value={cardData.name}
                  onChange={(value) => handleFieldChange('name', value)}
                />
              </Form.Item>
              
              <Form.Item label="公司名稱">
                <Input
                  placeholder="請輸入公司名稱"
                  value={cardData.company_name}
                  onChange={(value) => handleFieldChange('company_name', value)}
                />
              </Form.Item>
              
              <Form.Item label="職位">
                <Input
                  placeholder="請輸入職位"
                  value={cardData.position}
                  onChange={(value) => handleFieldChange('position', value)}
                />
              </Form.Item>
            </div>

            {/* 聯絡資訊 */}
            <div className="form-section">
              <Divider>聯絡資訊</Divider>
              
              <Form.Item label="手機">
                <Input
                  placeholder="請輸入手機號碼"
                  value={cardData.mobile_phone}
                  onChange={(value) => handleFieldChange('mobile_phone', value)}
                />
              </Form.Item>
              
              <Form.Item label="公司電話">
                <Input
                  placeholder="請輸入公司電話"
                  value={cardData.office_phone}
                  onChange={(value) => handleFieldChange('office_phone', value)}
                />
              </Form.Item>
              
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

            {/* 地址資訊 */}
            <div className="form-section">
              <Divider>地址資訊</Divider>
              
              <Form.Item label="公司地址一">
                <Input
                  placeholder="請輸入公司地址"
                  value={cardData.company_address_1}
                  onChange={(value) => handleFieldChange('company_address_1', value)}
                />
              </Form.Item>
              
              <Form.Item label="公司地址二">
                <Input
                  placeholder="請輸入公司地址（補充）"
                  value={cardData.company_address_2}
                  onChange={(value) => handleFieldChange('company_address_2', value)}
                />
              </Form.Item>
            </div>

            {/* 備註 */}
            <div className="form-section">
              <Divider>其他資訊</Divider>
              
              <Form.Item label="備註">
                <TextArea
                  placeholder="請輸入備註資訊"
                  rows={3}
                  value={cardData.notes}
                  onChange={(value) => handleFieldChange('notes', value)}
                />
              </Form.Item>
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
          <Button 
            color="default" 
            size="large" 
            block 
            onClick={handleReset}
            disabled={loading}
          >
            重置表單
          </Button>
        </Space>
      </div>
    </div>
  );
};

export default AddCardPage; 