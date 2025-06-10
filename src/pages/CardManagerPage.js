import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Card, 
  Button, 
  Space, 
  Toast, 
  NavBar,
  Modal,
  Tag,
  SearchBar,
  Divider,
  Empty
} from 'antd-mobile';
import { 
  DeleteOutline, 
  EditSOutline, 
  DownlandOutline, 
  AddOutline,
  UserContactOutline,
  PhoneFill,
  MailOutline,
  EnvironmentOutline
} from 'antd-mobile-icons';
import axios from 'axios';

const CardManagerPage = () => {
  const navigate = useNavigate();
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [filteredCards, setFilteredCards] = useState([]);

  // 載入名片列表
  const loadCards = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/v1/cards/');
      if (response.data) {
        setCards(response.data);
        setFilteredCards(response.data);
      }
    } catch (error) {
      console.error('載入名片失敗:', error);
      Toast.show({
        content: '載入名片失敗',
        position: 'center',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCards();
  }, []);

  // 搜索功能
  useEffect(() => {
    if (!searchText.trim()) {
      setFilteredCards(cards);
    } else {
      const filtered = cards.filter(card => 
        (card.name && card.name.toLowerCase().includes(searchText.toLowerCase())) ||
        (card.company_name && card.company_name.toLowerCase().includes(searchText.toLowerCase())) ||
        (card.position && card.position.toLowerCase().includes(searchText.toLowerCase())) ||
        (card.mobile_phone && card.mobile_phone.includes(searchText)) ||
        (card.office_phone && card.office_phone.includes(searchText)) ||
        (card.email && card.email.toLowerCase().includes(searchText.toLowerCase()))
      );
      setFilteredCards(filtered);
    }
  }, [searchText, cards]);

  // 刪除名片
  const handleDeleteCard = async (cardId) => {
    Modal.confirm({
      content: '確定要刪除這張名片嗎？',
      onConfirm: async () => {
        try {
          await axios.delete(`/api/v1/cards/${cardId}`);
          Toast.show({
            content: '刪除成功',
            position: 'center',
          });
          loadCards(); // 重新載入列表
        } catch (error) {
          console.error('刪除失敗:', error);
          Toast.show({
            content: '刪除失敗',
            position: 'center',
          });
        }
      },
    });
  };

  // 匯出名片
  const handleExport = async (format) => {
    try {
      const response = await axios.get(`/api/v1/cards/export/download?format=${format}`, {
        responseType: 'blob',
      });
      
      // 創建下載鏈接
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const fileExtension = format === 'excel' ? 'xlsx' : (format === 'vcard' ? 'vcf' : 'csv');
      link.setAttribute('download', `cards.${fileExtension}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      Toast.show({
        content: `${format.toUpperCase()}匯出成功`,
        position: 'center',
      });
    } catch (error) {
      console.error('匯出失敗:', error);
      Toast.show({
        content: '匯出失敗',
        position: 'center',
      });
    }
  };

  // 渲染名片項目
  const renderCardItem = (card) => (
    <Card 
      key={card.id} 
      style={{ marginBottom: '12px', cursor: 'pointer' }}
      bodyStyle={{ padding: '16px' }}
      onClick={() => navigate(`/cards/${card.id}`)}
    >
      <div className="card-content">
        {/* 基本資訊 */}
        <div className="card-header" style={{ marginBottom: '12px' }}>
          <div className="name-company" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <UserContactOutline style={{ color: '#1890ff' }} />
            <div>
              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#262626' }}>
                {card.name || '未知姓名'}
              </div>
              {card.company_name && (
                <div style={{ fontSize: '14px', color: '#8c8c8c' }}>
                  {card.company_name}
                </div>
              )}
            </div>
          </div>
          {card.position && (
            <Tag color="blue" style={{ marginTop: '4px' }}>
              {card.position}
            </Tag>
          )}
        </div>

        {/* 聯絡資訊 */}
        <div className="contact-info" style={{ marginBottom: '12px' }}>
          {card.mobile_phone && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <PhoneFill style={{ color: '#52c41a', fontSize: '14px' }} />
              <span style={{ fontSize: '14px' }}>手機: {card.mobile_phone}</span>
            </div>
          )}
          {card.office_phone && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <PhoneFill style={{ color: '#1890ff', fontSize: '14px' }} />
              <span style={{ fontSize: '14px' }}>公司: {card.office_phone}</span>
            </div>
          )}
          {card.email && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <MailOutline style={{ color: '#fa8c16', fontSize: '14px' }} />
              <span style={{ fontSize: '14px' }}>{card.email}</span>
            </div>
          )}
          {(card.company_address_1 || card.company_address_2) && (
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '4px' }}>
              <EnvironmentOutline style={{ color: '#eb2f96', fontSize: '14px', marginTop: '2px' }} />
              <div style={{ fontSize: '14px', lineHeight: '1.4' }}>
                {card.company_address_1}
                {card.company_address_2 && <div>{card.company_address_2}</div>}
              </div>
            </div>
          )}
        </div>

        {/* 其他資訊 */}
        {(card.line_id || card.notes) && (
          <div className="extra-info" style={{ marginBottom: '12px' }}>
            {card.line_id && (
              <div style={{ fontSize: '14px', color: '#8c8c8c', marginBottom: '4px' }}>
                Line ID: {card.line_id}
              </div>
            )}
            {card.notes && (
              <div style={{ fontSize: '14px', color: '#8c8c8c' }}>
                備註: {card.notes}
              </div>
            )}
          </div>
        )}

        {/* 操作按鈕 */}
        <div className="card-actions" style={{ borderTop: '1px solid #f0f0f0', paddingTop: '12px' }}>
          <Space>
            <Button 
              size="small" 
              color="primary" 
              fill="outline"
              onClick={(e) => {
                e.stopPropagation(); // 防止觸發卡片點擊事件
                navigate(`/cards/${card.id}`);
              }}
            >
              <EditSOutline /> 編輯
            </Button>
            <Button 
              size="small" 
              color="danger" 
              fill="outline"
              onClick={(e) => {
                e.stopPropagation(); // 防止觸發卡片點擊事件
                handleDeleteCard(card.id);
              }}
            >
              <DeleteOutline /> 刪除
            </Button>
          </Space>
        </div>
      </div>
    </Card>
  );

  return (
    <div className="card-manager-page">
      <NavBar onBack={() => navigate('/')}>名片管理</NavBar>
      
      <div className="content" style={{ padding: '16px' }}>
        {/* 搜索欄 */}
        <SearchBar
          placeholder="搜索名片（姓名、公司、電話、郵箱）"
          value={searchText}
          onChange={setSearchText}
          style={{ marginBottom: '16px' }}
        />

        {/* 操作按鈕 */}
        <Card style={{ marginBottom: '16px' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Space style={{ width: '100%' }}>
              <Button 
                color="primary" 
                size="large" 
                style={{ flex: 1 }}
                onClick={() => navigate('/add-card')}
              >
                <AddOutline /> 手動新增
              </Button>
              <Button 
                color="default" 
                size="large" 
                style={{ flex: 1 }}
                onClick={() => navigate('/scan')}
              >
                <AddOutline /> OCR掃描
              </Button>
            </Space>
            
            <Divider>匯出功能</Divider>
            
            <Space style={{ width: '100%' }}>
              <Button 
                color="default" 
                fill="outline"
                style={{ flex: 1 }}
                onClick={() => handleExport('csv')}
              >
                <DownlandOutline /> CSV
              </Button>
              <Button 
                color="default" 
                fill="outline"
                style={{ flex: 1 }}
                onClick={() => handleExport('excel')}
              >
                <DownlandOutline /> Excel
              </Button>
              <Button 
                color="default" 
                fill="outline"
                style={{ flex: 1 }}
                onClick={() => handleExport('vcard')}
              >
                <DownlandOutline /> vCard
              </Button>
            </Space>
          </Space>
        </Card>

        {/* 名片列表 */}
        <div className="cards-list">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <div>載入中...</div>
            </div>
          ) : filteredCards.length === 0 ? (
            <Empty
              style={{ padding: '40px' }}
              description={
                searchText ? `沒有找到包含 "${searchText}" 的名片` : "還沒有名片，點擊上方按鈕新增"
              }
            />
          ) : (
            <div>
              <div style={{ marginBottom: '12px', color: '#8c8c8c', fontSize: '14px' }}>
                共 {filteredCards.length} 張名片
              </div>
              {filteredCards.map(renderCardItem)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CardManagerPage; 