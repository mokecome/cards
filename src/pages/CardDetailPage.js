import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Card, 
  Button, 
  Space, 
  Toast, 
  NavBar,
  Form,
  Input,
  TextArea,
  Divider,
  Loading,
  Dialog
} from 'antd-mobile';
import { 
  CheckOutline, 
  UserContactOutline, 
  EditSOutline, 
  EyeOutline,
  DeleteOutline
} from 'antd-mobile-icons';
import axios from 'axios';

const CardDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  
  // 統一的名片資料狀態 - 與OCR掃描頁面保持一致的9個欄位
  const [cardData, setCardData] = useState({
    id: '',
    name: '',                    // 姓名
    company_name: '',            // 公司名稱
    position: '',                // 職位
    mobile_phone: '',            // 手機
    office_phone: '',            // 公司電話
    email: '',                   // Email
    line_id: '',                 // Line ID
    notes: '',                   // 備註
    company_address_1: '',       // 公司地址一
    company_address_2: '',       // 公司地址二
    created_at: '',              // 創建時間
    updated_at: ''               // 更新時間
  });

  // 載入名片資料
  useEffect(() => {
    loadCardData();
  }, [id]);

  const loadCardData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/v1/cards/${id}`);
      if (response.data) {
        setCardData(response.data);
      }
    } catch (error) {
      console.error('載入名片失敗:', error);
      Toast.show({
        content: '載入名片資料失敗',
        position: 'center',
      });
      navigate('/cards');
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

  // 切換編輯模式
  const toggleEditMode = () => {
    if (isEditing) {
      // 如果正在編輯，詢問是否取消編輯
      Dialog.confirm({
        content: '是否取消編輯？未保存的更改將會丟失。',
        onConfirm: () => {
          setIsEditing(false);
          loadCardData(); // 重新載入原始資料
        }
      });
    } else {
      setIsEditing(true);
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

    setSaving(true);
    try {
      const saveData = new FormData();
      
      // 添加名片資料
      Object.keys(cardData).forEach(key => {
        if (key !== 'id' && key !== 'created_at' && key !== 'updated_at' && cardData[key]) {
          saveData.append(key, cardData[key]);
        }
      });

      const response = await axios.put(`/api/v1/cards/${id}/`, saveData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data) {
        Toast.show({
          content: '名片更新成功！',
          position: 'center',
        });
        setIsEditing(false);
        // 重新載入資料以更新時間戳等信息
        loadCardData();
      }
    } catch (error) {
      console.error('保存失敗:', error);
      Toast.show({
        content: error.response?.data?.detail || '保存失敗，請重試',
        position: 'center',
      });
    } finally {
      setSaving(false);
    }
  };

  // 刪除名片
  const handleDelete = () => {
    Dialog.confirm({
      content: '確定要刪除這張名片嗎？此操作無法復原。',
      confirmText: '刪除',
      onConfirm: async () => {
        try {
          await axios.delete(`/api/v1/cards/${id}`);
          Toast.show({
            content: '名片已刪除',
            position: 'center',
          });
          navigate('/cards');
        } catch (error) {
          console.error('刪除失敗:', error);
          Toast.show({
            content: '刪除失敗，請重試',
            position: 'center',
          });
        }
      }
    });
  };

  // 格式化日期
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="card-detail-page">
        <NavBar onBack={() => navigate('/cards')}>名片詳情</NavBar>
        <div style={{ padding: '50px', textAlign: 'center' }}>
          <Loading />
        </div>
      </div>
    );
  }

  return (
    <div className="card-detail-page">
      <NavBar 
        onBack={() => navigate('/cards')}
        right={
          <Space>
            <Button 
              size="mini" 
              color={isEditing ? 'default' : 'primary'} 
              onClick={toggleEditMode}
            >
              {isEditing ? <EyeOutline /> : <EditSOutline />}
              {isEditing ? '取消' : '編輯'}
            </Button>
          </Space>
        }
      >
        名片詳情
      </NavBar>
      
      <div className="content" style={{ padding: '16px' }}>
        {/* 名片資料顯示/編輯表單 */}
        <Card 
          title={isEditing ? "編輯名片資料" : "名片資料"} 
          extra={<UserContactOutline />} 
          style={{ marginBottom: '16px' }}
        >
          <Form layout="vertical">
            {/* 基本資訊 */}
            <div className="form-section">
              <Divider>基本資訊</Divider>
              
              <Form.Item label="姓名 *" required>
                {isEditing ? (
                  <Input
                    placeholder="請輸入姓名"
                    value={cardData.name}
                    onChange={(value) => handleFieldChange('name', value)}
                  />
                ) : (
                  <div style={{ padding: '8px 0', fontSize: '16px' }}>
                    {cardData.name || '-'}
                  </div>
                )}
              </Form.Item>
              
              <Form.Item label="公司名稱">
                {isEditing ? (
                  <Input
                    placeholder="請輸入公司名稱"
                    value={cardData.company_name}
                    onChange={(value) => handleFieldChange('company_name', value)}
                  />
                ) : (
                  <div style={{ padding: '8px 0', fontSize: '16px' }}>
                    {cardData.company_name || '-'}
                  </div>
                )}
              </Form.Item>
              
              <Form.Item label="職位">
                {isEditing ? (
                  <Input
                    placeholder="請輸入職位"
                    value={cardData.position}
                    onChange={(value) => handleFieldChange('position', value)}
                  />
                ) : (
                  <div style={{ padding: '8px 0', fontSize: '16px' }}>
                    {cardData.position || '-'}
                  </div>
                )}
              </Form.Item>
            </div>

            {/* 聯絡資訊 */}
            <div className="form-section">
              <Divider>聯絡資訊</Divider>
              
              <Form.Item label="手機">
                {isEditing ? (
                  <Input
                    placeholder="請輸入手機號碼"
                    value={cardData.mobile_phone}
                    onChange={(value) => handleFieldChange('mobile_phone', value)}
                  />
                ) : (
                  <div style={{ padding: '8px 0', fontSize: '16px' }}>
                    {cardData.mobile_phone || '-'}
                  </div>
                )}
              </Form.Item>
              
              <Form.Item label="公司電話">
                {isEditing ? (
                  <Input
                    placeholder="請輸入公司電話"
                    value={cardData.office_phone}
                    onChange={(value) => handleFieldChange('office_phone', value)}
                  />
                ) : (
                  <div style={{ padding: '8px 0', fontSize: '16px' }}>
                    {cardData.office_phone || '-'}
                  </div>
                )}
              </Form.Item>
              
              <Form.Item label="Email">
                {isEditing ? (
                  <Input
                    placeholder="請輸入Email地址"
                    value={cardData.email}
                    onChange={(value) => handleFieldChange('email', value)}
                  />
                ) : (
                  <div style={{ padding: '8px 0', fontSize: '16px' }}>
                    {cardData.email || '-'}
                  </div>
                )}
              </Form.Item>
              
              <Form.Item label="Line ID">
                {isEditing ? (
                  <Input
                    placeholder="請輸入Line ID"
                    value={cardData.line_id}
                    onChange={(value) => handleFieldChange('line_id', value)}
                  />
                ) : (
                  <div style={{ padding: '8px 0', fontSize: '16px' }}>
                    {cardData.line_id || '-'}
                  </div>
                )}
              </Form.Item>
            </div>

            {/* 地址資訊 */}
            <div className="form-section">
              <Divider>地址資訊</Divider>
              
              <Form.Item label="公司地址一">
                {isEditing ? (
                  <Input
                    placeholder="請輸入公司地址"
                    value={cardData.company_address_1}
                    onChange={(value) => handleFieldChange('company_address_1', value)}
                  />
                ) : (
                  <div style={{ padding: '8px 0', fontSize: '16px' }}>
                    {cardData.company_address_1 || '-'}
                  </div>
                )}
              </Form.Item>
              
              <Form.Item label="公司地址二">
                {isEditing ? (
                  <Input
                    placeholder="請輸入公司地址（補充）"
                    value={cardData.company_address_2}
                    onChange={(value) => handleFieldChange('company_address_2', value)}
                  />
                ) : (
                  <div style={{ padding: '8px 0', fontSize: '16px' }}>
                    {cardData.company_address_2 || '-'}
                  </div>
                )}
              </Form.Item>
            </div>

            {/* 備註 */}
            <div className="form-section">
              <Divider>其他資訊</Divider>
              
              <Form.Item label="備註">
                {isEditing ? (
                  <TextArea
                    placeholder="請輸入備註資訊"
                    rows={3}
                    value={cardData.notes}
                    onChange={(value) => handleFieldChange('notes', value)}
                  />
                ) : (
                  <div style={{ padding: '8px 0', fontSize: '16px', whiteSpace: 'pre-wrap' }}>
                    {cardData.notes || '-'}
                  </div>
                )}
              </Form.Item>
            </div>

            {/* 時間資訊 */}
            {!isEditing && (
              <div className="form-section">
                <Divider>時間資訊</Divider>
                
                <Form.Item label="創建時間">
                  <div style={{ padding: '8px 0', fontSize: '14px', color: '#999' }}>
                    {formatDate(cardData.created_at)}
                  </div>
                </Form.Item>
                
                <Form.Item label="更新時間">
                  <div style={{ padding: '8px 0', fontSize: '14px', color: '#999' }}>
                    {formatDate(cardData.updated_at)}
                  </div>
                </Form.Item>
              </div>
            )}
          </Form>
        </Card>

        {/* 操作按鈕 */}
        <Space direction="vertical" style={{ width: '100%' }}>
          {isEditing ? (
            <Button 
              color="primary" 
              size="large" 
              block 
              onClick={handleSave}
              disabled={saving}
            >
              <CheckOutline /> 保存修改
            </Button>
          ) : (
            <Button 
              color="danger" 
              size="large" 
              block 
              onClick={handleDelete}
            >
              <DeleteOutline /> 刪除名片
            </Button>
          )}
        </Space>
      </div>
    </div>
  );
};

export default CardDetailPage; 