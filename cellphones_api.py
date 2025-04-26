import requests
import threading
from fake_useragent import UserAgent
import pprint
import json

ua = UserAgent()

url = 'https://api.cellphones.com.vn/v2/graphql/query'

# ...
url_1 = 'https://api.cellphones.com.vn/graphql-dashboard/graphql/query'
query_1 = "query check_applied_promotion {\n                      applied_promotion_with(oldProductId: 76013) \n                    }"

# Comment
url_2 = 'https://api.cellphones.com.vn/graphql-customer/graphql/query'
query_2 = '''
  query COMMENTS {
    comment(
      type: "product"
      pageUrl: "https://cellphones.com.vn/laptop-gaming-acer-nitro-v-anv15-51-55ca.html"
      productId: 75443
      currentPage: 1
    ) {
      total
      matches {
        id
        content
        page_name
        is_shown
        is_admin
        is_pinned
        sent_from
        created_at
        children
        product_id
        page_url
        customer {
          id
          fullname
        }
      }
    }
  }
'''

# Danh sách cửa hàng còn hàng
url_4 = 'https://api.cellphones.com.vn/graphql-dashboard/graphql/query'
query_4 = "query SHOP_STOCK {\n                          shops_stock(productId: 76016, provinceId: 30) {\n                            district_id\n                            district_name\n                            province_id\n                            province_name\n                            shops {\n                              id\n                              external_id\n                              district_id\n                              province_id\n                              address\n                              phone\n                              near\n                              google_link\n                            }\n                          }\n                        }"

# ID mua kèm giá sốc
url_5 = 'https://api.cellphones.com.vn/recommendation/v1/recommend'

# Mua kèm giá sốc
# url_10 = 'https://api.cellphones.com.vn/v2/graphql/query'
# query_10 = '''
#   query products {
#     products(
#       filter: {
#         static: {
#           province_id: 30
#           product_id: [
#             "96037", "87130", "99967", "80656", "51534", "84611",
#             "95676", "78719", "89813", "79777", "79775", "96496"
#           ]
#           is_parent: ["false", "true"]
#         }
#       }
#       size: 50
#     ) {
#       filterable {
#         name
#         price
#         thumbnail
#         parent_id
#         product_id
#         special_price
#         stock_available_id
#       }
#     }
# }
# '''

# Price cũ mới
url_11 = 'https://api.cellphones.com.vn/v2/graphql/query'
query_11 = '''
  query PRODUCT {
    product(
      id: "75443",
      provinceId: 30
    ) {
      filterable {
        price
        special_price
      }
    }
  }
'''


url_12 = 'https://api.sforum.vn/graphql/query'
query_12 = "\n                query posts {\n                  posts(\n                    filter: {include: {\n                      tag_slugs:[\"laptop-gaming-acer-nitro-v-anv15-51-55ca\"]\n                    }}\n                    paginator: {size: 5, page: 1}\n                    sort: [ { field: \"published_at\", direction: \"desc\" } ]\n                  ) {\n                    posts {\n                      id\n                      title\n                      slug\n                      thumbnail\n                      short_description\n                      scheduled_at\n                      created_at\n                      updated_at\n                      author {\n                        id\n                        first_name\n                        last_name\n                        slug\n                        profile {\n                          avatar\n                          description\n                        }\n                        total_posts\n                      }\n                    }\n                  }\n                }"

# url_13 = 'https://script.crazyegg.com/pages/data-scripts/0098/7283/site/cellphones.com.vn.json?t=1'
# query_13 = 

# Bảo hiểm mở rộng
url_14 = 'https://api.cellphones.com.vn/graphql-dashboard/graphql/query'
query_14 = "query warranty {\n                      extended_warranty(warranty_product: {product_id: 76013, categories: [380,729,933,1055,1434,1547,871], product_price: 27990000}) {\n                        product_id\n                        warranty_url\n                        warranty_packs {\n                          pack_id\n                          pack_code\n                          pack_title\n                          pack_tooltip\n                          value\n                        }\n                      }\n                    }"

# ...
url_15 = 'https://api.cellphones.com.vn/graphql-dashboard/graphql/query'
query_15 = "query trade_product{\n                            trade_products(productId: 76013 tradeType: 1) {\n                                exchange_products {\n                                    webId\n                                    name\n                                    brand\n                                    justActivated\n                                    thuLoai1\n                                    thuLoai2\n                                    thuLoai3\n                                    thuLoai4\n                                    text\n                                    troGia\n                                }\n                                applied_promotion_width\n                            }\n                        }"

# Sản phẩm tương tự 
url_16 = 'https://api.cellphones.com.vn/v2/graphql/query'
query_16 = "query SimilarProducts {\n                  products(\n                    filter: {\n                      static: {\n                      is_parent: \"true\"\n                      \n                      categories : [\"380\",\"933\",\"1055\",\"1434\",\"1547\",\"933\"]\n                      province_id: 30,\n                      \n                      ,filter_price: {\n                        from: 22311000, to: 27269000\n                      },\n                      }\n                      \n                    }\n                    sort: [{view: desc}]\n                    size: 10\n                  ) {\n                   \n       filterable{\n                      price\n                      special_price\n                      stock\n                      thumbnail\n                      promotion_pack\n                      sticker\n                      product_id\n                      filter_price\n                      price\n                      sticker\n                      special_price\n                      stock_available_id\n                      stock\n                      filter{\n                        id\n                        value\n                      }\n                   }\n                   general {\n                      url_path\n                      doc_quyen\n                      url_key\n                      manufacturer\n                      name\n                      product_id\n                      review {\n                          total_count\n                          average_rating\n                      }\n                    }\n                  }\n                }"

# Phụ kiện mua cùng
url_17 = 'https://api.cellphones.com.vn/v2/graphql/query'
query_17 = '''
  query getProductListByArrayId {
    products(
      filter: {
        static: {
          is_parent: "true"
          province_id: 30
          product_id: [
            "50100", "100555", "46416"
          ]
          stock: {
            from: 1
          }
          # stock_available_id: [46, 4920]
        }
      }
      sort: [{ view: desc }]
      # size: 3
    ) {
      general {
        product_id
        url_path
        name
        child_product
        doc_quyen
        attributes
        categories {
          categoryId
          level
          name
          uri
          similar
        }
      }
      filterable {
        sticker
        is_installment
        stock_available_id
        company_stock_id
        is_parent
        price
        prices
        special_price
        promotion_information
        thumbnail
        promotion_pack
        flash_sale_types
      }
    }
  }
'''

# All
url_18 = 'https://api.cellphones.com.vn/v2/graphql/query'
query_18 = '''
  query GetProductsByCateId {
    products(
      filter: {
        static: {
          categories: ["380"]
          province_id: 30
          stock: { from: 0 }
          # stock_available_id: [46, 56, 152, 4920]
          filter_price: { from: 1, to: 194990000 }
        }
        dynamic: {
          # Trường dynamic hiện đang để trống
        }
      }
      # page: 1
      size: 5000
      sort: [{ view: desc }]
    ) {
      general {
        product_id
        name
        attributes
        sku
        doc_quyen
        manufacturer
        url_key
        url_path
        categories {
          categoryId
          name
          uri
        }
        review {
          total_count
          average_rating
        }
      }
      filterable {
        is_installment
        stock_available_id
        company_stock_id
        filter {
          id
          Label
        }
        is_parent
        price
        prices
        special_price
        promotion_information
        thumbnail
        promotion_pack
        sticker
        flash_sale_types
      }
    }
  }
'''

url_19 = 'https://api.cellphones.com.vn/v2/graphql/query'
query_19 = " query{\n                             total(filter: {\n                                static: {\n                                  categories: [\"380\"],\n                                  province_id: 30,\n                                  stock: {\n                                    from: 0\n                                  },\n                                  stock_available_id: [46, 56, 152, 4920],\n                                  filter_price: {from:1to:194990000}\n                                }\n                                dynamic: {\n                                    \n                                    \n                                }\n                            })\n                        }"

headers = {
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9,vi;q=0.8,hy;q=0.7',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'origin': 'https://cellphones.com.vn',
    'pragma': 'no-cache',
    'referer': 'https://cellphones.com.vn/',
    'user-agent': ua.random,
}

query = """
query getDataProductChild {
  products(
    filter: {
      static: {
        is_parent: "false",
        product_id: ["76016"],
        province_id: 30
      }
    },
    sort: [{ view: desc }],
    size: 9
  ) {
    filterable {
      price
      special_price
      stock
      thumbnail
      member_promotion
      prices
      stock_available_id
      categories
      company_stock_id
      allow_cart_types
    }
    general {
      attributes
      url_path
      name
      product_id
      sku
      categories {
        categoryId
        name
        uri
      }
    }
  }
}
"""


# ----------------------------------------------------------  RESULT  ----------------------------------------------------------

# GetProductsByCateId ['data']['product'] (URL 18)
'''
{
  'product_id': 75443,
  'name': 'Laptop Gaming Acer Nitro V ANV15-51-58AN',
  'attributes': {
    'additional_information': 'I5-13420H/16GB/512GB PCIE/VGA 4GB RTX2050/15.6 FHD 144HZ/WIN11/ĐEN',
    'ads_base_image': '/t/e/text_ng_n_9__4_4.png',
    'bao_hanh_1_doi_1': True,
    'basic': [
      
    ],
    'battery': '4 cell - 57 Wh', 
    'best_discount_price': '2653.0000', ❌
    'bluetooth': 'Bluetooth 5.1', 
    'change_layout_preorder': 'Liên hệ CSKH', ❌
    'coupon_value': '2653.0000', ❌
    'cpu': 'Intel Core i5-13420H (8 lõi / 12 luồng, up to 4.60 GHz, 12 MB Intel Smart Cache)', 
    'dimensions': '362.3 x 239.89 x 22.9 - 26.9 mm (W x D x H)',
    'discount_price': '2653.0000', ❌
    'display_resolution': '1920 x 1080 pixels (FullHD)',
    'display_size': '15.6 inches',
    'display_type': '250 nits<br>Acer ComfyView LED-backlit TFT LCD<br>45% NTSC',
    'fe_minimum_down_payment': '0.1',
    'final_sale_price': '2653.0000', ❌
    'flash_sale_from': '2019-01-01 00:00:00',
    'flash_sale_price': '2653.0000',
    'full_by_group': [
      
    ],
    'hc_maximum_down_payment': '0.7', ❌
    'hc_minimum_down_payment': '0.3', ❌
    'hdd_sdd': '512GB',
    'id': 75443,
    'image': '/t/e/text_d_i_3__3_19.png',
    'image_label': 'Laptop Gaming Acer Nitro V ANV15-51-58AN',
    'included_accessories': 'Máy, sạc, sách hướng dẫn</p><p style="color: red;"><a href="https://www.acervietnam.com.vn/bao-hanh-3s1"><span style="color: #ff0000;">T&igrave;m hiểu th&ecirc;m về bảo h&agrave;nh VIP 3S1</span></a></p>',
    'is_imported': True,
    'key_selling_points': '<ul><li>CPU Intel Core i5-13420H c&acirc;n mọi tựa game từ AAA đến game Esport.</li><li>GPU GeForce RTX 2050 mới nhất cho đồ họa cực đỉnh, chiến mọi tựa game với mức c&agrave;i đặt cao.</li><li>RAM 16 GB DDR5 5200Mhz, khả năng xử l&yacute; đa nhiệm v&agrave; đa t&aacute;c vụ của m&aacute;y c&agrave;ng được tăng tốc tối đa.</li><li>M&agrave;n h&igrave;nh 15.6 inch Full HD, tần số qu&eacute;t chuẩn chiến game 144Hz.</li><li>Ổ cứng&nbsp;512GB PCIE rộng r&atilde;i, lưu mọi tựa game dễ d&agrave;ng.</li></ul>',
    'laptop_cam_ung': 'Không',
    'laptop_camera_webcam': '720p HD',
    'laptop_cong_nghe_am_thanh': 'DTS® X:Ultra',
    'laptop_cpu': 'Intel Core i5',
    'laptop_filter_gpu': 'RTX 2050',
    'laptop_filter_tac_vu_su_dung': 'Đồ hoạ 3D, chỉnh sửa video',
    'laptop_loai_den_ban_phim': 'Led trắng',
    'laptop_loai_ram': 'DDR5 5200MHz',
    'laptop_nganh_hoc': 'Lập trình ',
    'laptop_ram': '16GB',
    'laptop_resolution_filter': 'Full HD',
    'laptop_screen_size_filter': 'Trên 15 inch',
    'laptop_so_khe_ram': '2 khe (2 x 8GB, máy nguyên bản 8GB, được tặng 8GB, nâng cấp tối đa 32GB) ',
    'laptop_special_feature': 'Ổ cứng SSD',
    'laptop_tam_nen_man_hinh': 'Tấm nền IPS',
    'laptop_tan_so_quet': '144 Hz',
    'laptop_vga_filter': 'NVIDIA GeForce Series',
    'loaisp': 'Chính hãng',
    'macbook_anh_bao_mat': 'no_selection',
    'macbook_anh_dong_chip': 'no_selection',
    'manufacturer': 'Acer',
    'meta_image': '/t/e/text_d_i_3__3_19.png',
    'meta_title': 'Laptop Acer Nitro V | Cấu hình khủng, tiết kiệm 1.5 triệu', ❌
    'mobile_accessory_type': '-',
    'msrp': '2653.0000', ❌
    'msrp_display_actual_price_type': '4', ❌
    'msrp_enabled': '2', ❌
    'nhu_cau_su_dung': 'Gaming',
    'o_cung_laptop': '512GB PCIe NVMe SSD (2 khe cắm, nâng cấp tối đa 2TB SSD)',
    'options_container': 'container2',
    'os_version': 'Windows 11 Home',
    'ports_slots': '1x USB Type-C <br> 3x USB-A <br> 1x Ethernet (RJ-45) <br> 1x DC-in jack for AC adapter<br> 1x HDMI 2.1 (hỗ trợ HDCP)<br> 1x 3.5 mm headphone/speaker jack',
    'product_condition': 'Mới',
    'product_feed_type': 'Normal',
    'product_id': 75443,
    'product_state': 'Nguyên hộp, đầy đủ phụ kiện từ nhà sản xuất<br> Bảo hành pin và bộ sạc 12 tháng',
    'product_weight': '2.1 kg',
    'related_name': 'i5-13420H<br>16GB - 512GB<br>RTX 2050',
    'short_description_hidden_time': '2020-12-31 00:00:00',
    'short_description_show_time': '2020-01-01 00:00:00',
    'sim_special_group': 'GỌI THẢ GA, DATA KHỦNG', ❌
    'small_image': '/t/e/text_d_i_3__3_19.png',
    'small_image_label': 'Laptop Gaming Acer Nitro V ANV15-51-58AN', 
    'smember_sms': 'SMS', ❌
    'special_price': '2653.0000',
    'status': True,
    'tag_sforum': 'laptop-gaming-acer-nitro-v-anv15-51-58an',
    'tax_vat': True,
    'thumbnail_label': 'Laptop Gaming Acer Nitro V ANV15-51-58AN',
    'tien_coc': '2653.0000', ❌
    'title_price': 'Giá chính thức',
    'url_key': 'laptop-gaming-acer-nitro-v-anv15-51-58an',
    'url_path': 'laptop-gaming-acer-nitro-v-anv15-51-58an.html',
    'use_smd_colorswatch': True, ❌
    'vga': 'NVIDIA GeForce RTX 2050 4 GB GDDR6 VRAM',
    'warranty_information': 'Bảo hành 24 tháng tại trung tâm bảo hành Chính hãng. 1 đổi 1 trong 30 ngày nếu có lỗi phần cứng từ nhà sản xuất. ',
    'weight': '2653.0000', ❌
    'wlan': '802.11a/b/g/n/ac+ax wireless LAN'
  },
  'sku': 'laptop-gaming-acer-nitro-v-anv15-51-58an',
  'doc_quyen': '',
  'manufacturer': 'Acer',
  'url_key': 'laptop-gaming-acer-nitro-v-anv15-51-58an',
  'url_path': 'laptop-gaming-acer-nitro-v-anv15-51-58an.html',
  'categories': [
    {
      'categoryId': 380,
      'name': 'Laptop',
      'uri': 'laptop'
    },
    {
      'categoryId': 729,
      'name': 'Acer',
      'uri': 'acer'
    },
    {
      'categoryId': 933,
      'name': 'Laptop Gaming',
      'uri': 'gaming'
    },
    {
      'categoryId': 1434,
      'name': 'Laptop 15.6 inch',
      'uri': 'laptop-15-6-inch'
    },
    {
      'categoryId': 1547,
      'name': 'Laptop core i5',
      'uri': 'core-i5'
    },
    {
      'categoryId': 871,
      'name': 'Nitro',
      'uri': 'nitro'
    }
  ],
  'review': {
    'total_count': 8,
    'average_rating': 5
  }
}
'''


# PRODUCT ['data']['product'] (URL 11)
'''
{
  "filterable": {
      "price": 2.149e+07,
      "special_price": 1.699e+07
  }
}
'''

# URL 5 -> ID for phụ kiện đi kèm
# response = requests.get(url_5, headers=headers, params={"product_id": '75443'})
'''
{
  'data': [
    {
      'product_id': 50100,
      'source': 'auto'
    },
    {
      'product_id': 100555,
      'source': 'auto'
    },
    {
      'product_id': 46416,
      'source': 'auto'
    }
  ],
  'input': 75443,
  'message': 'ok'
}
'''


# Phụ kiện đi kèm  (URL 17)
# response = requests.post(url_17, headers=headers, json={'query': query_17})
# data = response.json()
'''
{
  'data': {
    'products': [
      {
        'general': {
          'product_id': 50100,
          'url_path': 'ban-phim-co-gaming-predator-aethon-301-tkl.html',
          'name': 'Bàn Phím Cơ Gaming Predator Aethon TKL 301',
          'child_product': [
            71522
          ],
          'doc_quyen': '',
          'attributes': {
            'additional_information': 'IT.BP.111',
            'ads_base_image': '/b/a/ban-phim-co-gaming-predator-aethon-301-tkl.png',
            'banphim_den_led': 'Có',
            'bao_hanh_1_doi_1': True,
            'basic': [
              
            ],
            'best_discount_price': '155.0000',
            'change_layout_preorder': 'Liên hệ CSKH',
            'chat_lieu': 'Nhựa ABS ',
            'coupon_value': '155.0000',
            'discount_price': '155.0000',
            'fe_minimum_down_payment': '0.1',
            'final_sale_price': '155.0000',
            'flash_sale_from': '2019-01-01 00:00:00',
            'flash_sale_price': '155.0000',
            'full_by_group': [
              
            ],
            'gia_vo_doi': '155.0000',
            'hc_maximum_down_payment': '0.7',
            'hc_minimum_down_payment': '0.3',
            'id': 50100,
            'image': '/b/a/ban-phim-co-gaming-predator-aethon-301-tkl.png',
            'image_label': 'Bàn Phím Cơ Gaming Predator Aethon TKL 301 ',
            'loaisp': 'Chính hãng',
            'maychieu_tien_ich': 'Trang bị Switch Outemu Blue, lực nhấn 60g <br>  N-Key Rollover đầy đủ, đạt tiêu chuẩn 50 triệu lần nhấn',
            'meta_image': '/b/a/ban-phim-co-gaming-predator-aethon-301-tkl.png',
            'meta_title': 'Bàn Phím Cơ Gaming Predator Aethon TKL 301 | Giá rẻ',
            'mobile_accessory_type': 'Bàn',
            'msrp': '155.0000',
            'msrp_display_actual_price_type': '4',
            'msrp_enabled': '2',
            'options_container': 'container2',
            'phone_accessory_brands': 'Acer',
            'product_condition': 'Mới',
            'product_feed_type': 'Normal',
            'product_id': 50100,
            'product_state': 'Mới, đầy đủ phụ kiện từ nhà sản xuất',
            'promotion_percent': '155.0000',
            'short_description': '<div class="cps-additional-note">\r\n<p>Hotsale từ ng&agrave;y <span style="color: #ff0000;">25/8 - 27/8</span>&nbsp;: Giảm gi&aacute; chỉ c&ograve;n<span style="color: #ff0000;">&nbsp;990<span data-sheets-value="{&quot;1&quot;:2,&quot;2&quot;:&quot;19,990,000&quot;}" data-sheets-userformat="{&quot;2&quot;:513,&quot;3&quot;:{&quot;1&quot;:0},&quot;12&quot;:0}">.000</span>đ&nbsp;</span>(số lượng c&oacute; hạn, &aacute;p dụng c&ugrave;ng ưu đ&atilde;i Smember, kh&ocirc;ng &aacute;p dụng c&ugrave;ng chương tr&igrave;nh kh&aacute;c).</p>\r\n<p><span>Ng&agrave;y cuối hotsale</span><span>&nbsp;chỉ &aacute;p dụng thanh to&aacute;n online 100% hoặc thanh to&aacute;n trực tiếp tại cửa h&agrave;ng.</span></p>\r\n</div>',
            'short_description_hidden_time': '2023-08-27 00:00:00',
            'short_description_show_time': '2023-08-22 00:00:00',
            'sim_special_group': 'GỌI THẢ GA, DATA KHỦNG',
            'small_image': '/b/a/ban-phim-co-gaming-predator-aethon-301-tkl.png',
            'small_image_label': 'Bàn Phím Cơ Gaming Predator Aethon TKL 301 ',
            'smember_sms': 'SMS',
            'special_price': '155.0000',
            'status': True,
            'tag_sforum': 'ban-phim-co-gaming-predator-aethon-301-tkl',
            'tax_vat': True,
            'thumbnail_label': 'Bàn Phím Cơ Gaming Predator Aethon TKL 301 ',
            'tien_coc': '155.0000',
            'title_price': 'Giá chính thức',
            'url_key': 'ban-phim-co-gaming-predator-aethon-301-tkl',
            'url_path': 'ban-phim-co-gaming-predator-aethon-301-tkl.html',
            'use_smd_colorswatch': True,
            'visibility': True,
            'warranty_information': 'Bảo hành 3 tháng chính hãng. ',
            'weight': '155.0000'
          },
          'categories': [
            {
              'categoryId': 2,
              'level': 1,
              'name': 'Root',
              'uri': 'default-category',
              'similar': ''
            },
            {
              'categoryId': 30,
              'level': 2,
              'name': 'Phụ kiện',
              'uri': 'phu-kien',
              'similar': ''
            },
            {
              'categoryId': 663,
              'level': 3,
              'name': 'Chuột | Bàn Phím',
              'uri': 'chuot-ban-phim-may-tinh',
              'similar': '663'
            },
            {
              'categoryId': 665,
              'level': 4,
              'name': 'Bàn phím',
              'uri': 'ban-phim',
              'similar': '665'
            },
            {
              'categoryId': 1005,
              'level': 5,
              'name': 'Bàn phím Gaming',
              'uri': 'gaming',
              'similar': '1005'
            }
          ]
        },
        'filterable': {
          'sticker': {
            'black_friday': False,
            'show_flashsale': False,
            'uu_dai_tet': False
          },
          'is_installment': 0,
          'stock_available_id': 46,
          'company_stock_id': 46,
          'is_parent': True,
          'price': 2500000.0,
          'prices': {
            'root': {
              'chiet_khau': 0,
              'discount_id': 0,
              'discount_value': 0,
              'value': 2500000
            },
            'smem': {
              'chiet_khau': 30000,
              'discount_id': 0,
              'discount_value': 0,
              'value': 960000
            },
            'snew': {
              'chiet_khau': 20000,
              'discount_id': 0,
              'discount_value': 0,
              'value': 970000
            },
            'special': {
              'chiet_khau': 0,
              'discount_id': 4923,
              'discount_value': 1510000,
              'value': 990000
            },
            'svip': {
              'chiet_khau': 50000,
              'discount_id': 0,
              'discount_value': 0,
              'value': 941000
            }
          },
          'special_price': 990000,
          'promotion_information': '',
          'thumbnail': '/b/a/ban-phim-co-gaming-predator-aethon-301-tkl.png',
          'promotion_pack': {
            
          },
          'flash_sale_types': None
        }
      },
      {
        'general': {
          'product_id': 100555,
          'url_path': 'ram-transcend-ddr5-4800mhz-8gb.html',
          'name': 'RAM Laptop Transcend DDR5 4800MHz 8GB',
          'child_product': None,
          'doc_quyen': '',
          'attributes': {
            'additional_information': 'R.TC.03',
            'ads_base_image': '/g/r/group_770.png',
            'bao_hanh_1_doi_1': True,
            'basic': [
              
            ],
            'change_layout_preorder': 'Liên hệ CSKH',
            'flash_sale_from': '2019-01-01 00:00:00',
            'flash_sale_price': '0.0000',
            'full_by_group': [
              
            ],
            'id': 100555,
            'image': '/g/r/group_770.png',
            'image_label': 'RAM Laptop Transcend DDR5 4800MHz 8GB',
            'is_imported': True,
            'loaisp': 'Chính hãng',
            'meta_image': '/g/r/group_770.png',
            'meta_title': 'RAM Laptop Transcend DDR5 4800MHz 8GB | Giá rẻ',
            'mobile_accessory_type': '-',
            'msrp_display_actual_price_type': '4',
            'msrp_enabled': '2',
            'options_container': 'container2',
            'phone_accessory_brands': 'Transcend',
            'product_condition': 'Mới',
            'product_feed_type': 'Normal',
            'product_id': 100555,
            'product_state': 'Mới, đầy đủ phụ kiện từ nhà sản xuất',
            'ram_busram': '4800MHz',
            'ram_dungluong': '8GB',
            'ram_hotro': 'SO-DIMM (Laptop)',
            'ram_loairam': 'DDR5',
            'ram_rgb_led': 'Không hỗ trợ LED',
            'ram_timing': 'CL40',
            'ram_voltage': '1.1V',
            'short_description': '\r\n',
            'short_description_hidden_time': '2020-12-31 00:00:00',
            'short_description_show_time': '2020-01-01 00:00:00',
            'sim_special_group': 'GỌI THẢ GA, DATA KHỦNG',
            'small_image': '/g/r/group_770.png',
            'small_image_label': 'RAM Laptop Transcend DDR5 4800MHz 8GB',
            'smember_sms': 'SMS',
            'status': True,
            'tag_sforum': 'ram-transcend-ddr5-4800mhz-8gb',
            'tax_vat': True,
            'thumbnail_label': 'RAM Laptop Transcend DDR5 4800MHz 8GB',
            'tien_coc': '500000.0000',
            'title_price': 'Giá chính thức',
            'url_key': 'ram-transcend-ddr5-4800mhz-8gb',
            'url_path': 'ram-transcend-ddr5-4800mhz-8gb.html',
            'warranty_information': 'Bảo hành 60 tháng chính hãng. Miễn phí lắp đặt tại cửa hàng'
          },
          'categories': [
            {
              'categoryId': 705,
              'level': 2,
              'name': 'Linh kiện máy tính',
              'uri': 'linh-kien',
              'similar': ''
            },
            {
              'categoryId': 923,
              'level': 3,
              'name': 'RAM',
              'uri': 'ram',
              'similar': '923'
            },
            {
              'categoryId': 1029,
              'level': 4,
              'name': 'RAM 8GB',
              'uri': '8gb',
              'similar': ''
            },
            {
              'categoryId': 1559,
              'level': 4,
              'name': 'Ram DDR5',
              'uri': 'ddr5',
              'similar': ''
            }
          ]
        },
        'filterable': {
          'sticker': {
            'black_friday': False,
            'show_flashsale': False,
            'uu_dai_tet': False
          },
          'is_installment': 0,
          'stock_available_id': 46,
          'company_stock_id': 46,
          'is_parent': True,
          'price': 990000,
          'prices': {
            'root': {
              'chiet_khau': 0,
              'discount_id': 0,
              'discount_value': 0,
              'value': 990000
            },
            'smem': {
              'chiet_khau': 15000,
              'discount_id': 0,
              'discount_value': 0,
              'value': 735000
            },
            'smem_student': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'smem_teacher': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'snew': {
              'chiet_khau': 8000,
              'discount_id': 0,
              'discount_value': 0,
              'value': 743000
            },
            'snew_student': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'snew_teacher': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'snull_student': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'snull_teacher': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'special': {
              'chiet_khau': 0,
              'discount_id': 4923,
              'discount_value': 240000,
              'value': 750000
            },
            'svip': {
              'chiet_khau': 23000,
              'discount_id': 0,
              'discount_value': 0,
              'value': 728000
            },
            'svip_student': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'svip_teacher': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            }
          },
          'special_price': 750000,
          'promotion_information': '',
          'thumbnail': '/g/r/group_770.png',
          'promotion_pack': {
            
          },
          'flash_sale_types': None
        }
      },
      {
        'general': {
          'product_id': 46416,
          'url_path': 'ram-laptop-kingston-8gb-4800mt-s-ddr5-kvr48s40bs6-8.html',
          'name': 'Ram Laptop Kingston 8GB 4800MT/s DDR5 KVR48S40BS6-8',
          'child_product': None,
          'doc_quyen': '',
          'attributes': {
            'additional_information': 'PC.R.21',
            'ads_base_image': '/1/_/1_74_28.jpg',
            'bao_hanh_1_doi_1': True,
            'basic': [
              
            ],
            'best_discount_price': '220.0000',
            'change_layout_preorder': 'Liên hệ CSKH',
            'color': 'Đen',
            'cost': '220.0000',
            'coupon_value': '220.0000',
            'discount_price': '220.0000',
            'fe_minimum_down_payment': '0.1',
            'final_sale_price': '220.0000',
            'flash_sale_from': '2019-01-01 00:00:00',
            'flash_sale_price': '220.0000',
            'full_by_group': [
              
            ],
            'gia_vo_doi': '220.0000',
            'hc_maximum_down_payment': '0.7',
            'hc_minimum_down_payment': '0.3',
            'id': 46416,
            'image': '/g/r/group_304.png',
            'image_label': 'Ram Laptop Kingston 8GB 4800MT/s DDR5 KVR48S40BS6-8 ',
            'is_imported': True,
            'loaisp': 'Chính hãng',
            'meta_image': '/g/r/group_304.png',
            'meta_title': 'Ram Laptop Kingston 8GB 4800MT/s DDR5 KVR48S40BS6-8 | Giá rẻ\t',
            'mobile_accessory_type': 'Bàn',
            'msrp': '220.0000',
            'msrp_display_actual_price_type': '4',
            'msrp_enabled': '2',
            'options_container': 'container2',
            'phone_accessory_brands': 'Kingston',
            'product_condition': 'Mới',
            'product_feed_type': 'Normal',
            'product_id': 46416,
            'promotion_actual_price_id': '3063',
            'promotion_percent': '220.0000',
            'ram_busram': '4800MT/s',
            'ram_dungluong': '8GB',
            'ram_hotro': 'SO-DIMM (Laptop)',
            'ram_loairam': 'DDR5',
            'ram_timing': 'CL40',
            'ram_voltage': '1.1V',
            'short_description': '<div class="cps-additional-note">\r\n<p>TẾT "ANt" giảm sốc từ ng&agrave;y&nbsp;<span style="color: #ff0000;">2/2 -18/2</span>&nbsp;: Giảm gi&aacute; chỉ c&ograve;n<span style="color: #ff0000;">&nbsp;790,000<span data-sheets-value="{&quot;1&quot;:2,&quot;2&quot;:&quot;19,990,000&quot;}" data-sheets-userformat="{&quot;2&quot;:513,&quot;3&quot;:{&quot;1&quot;:0},&quot;12&quot;:0}"></span>đ&nbsp;</span>(số lượng c&oacute; hạn, &aacute;p dụng c&ugrave;ng ưu đ&atilde;i Smember).</p>\r\n<p><span>Ng&agrave;y cuối hotsale</span><span>&nbsp;chỉ &aacute;p dụng thanh to&aacute;n online 100% hoặc thanh to&aacute;n trực tiếp tại cửa h&agrave;ng.</span></p>\r\n</div>',
            'short_description_hidden_time': '2024-02-19 00:00:00',
            'short_description_show_time': '2024-01-31 00:00:00',
            'sim_special_group': 'GỌI THẢ GA, DATA KHỦNG',
            'small_image': '/g/r/group_304.png',
            'small_image_label': 'Ram Laptop Kingston 8GB 4800MT/s DDR5 KVR48S40BS6-8 ',
            'smember_sms': 'SMS',
            'special_from_date': '2022-05-26 00:00:00',
            'special_price': '220.0000',
            'status': True,
            'tag_sforum': 'ram-laptop-kingston-8gb-4800mt-s-ddr5-kvr48s40bs6-8',
            'tax_vat': True,
            'thumbnail_label': 'Ram Laptop Kingston 8GB 4800MT/s DDR5 KVR48S40BS6-8 ',
            'tien_coc': '220.0000',
            'title_price': 'Giá chính thức',
            'url_key': 'ram-laptop-kingston-8gb-4800mt-s-ddr5-kvr48s40bs6-8',
            'url_path': 'ram-laptop-kingston-8gb-4800mt-s-ddr5-kvr48s40bs6-8.html',
            'visibility': True,
            'warranty_information': 'Bảo hành 36 tháng chính hãng. Miễn phí dịch vụ lắp đặt tại cửa hàng.',
            'weight': '220.0000'
          },
          'categories': [
            {
              'categoryId': 705,
              'level': 2,
              'name': 'Linh kiện máy tính',
              'uri': 'linh-kien',
              'similar': ''
            },
            {
              'categoryId': 923,
              'level': 3,
              'name': 'RAM',
              'uri': 'ram',
              'similar': '923'
            },
            {
              'categoryId': 1029,
              'level': 4,
              'name': 'RAM 8GB',
              'uri': '8gb',
              'similar': ''
            },
            {
              'categoryId': 1559,
              'level': 4,
              'name': 'Ram DDR5',
              'uri': 'ddr5',
              'similar': ''
            },
            {
              'categoryId': 1573,
              'level': 4,
              'name': 'Ram Kingston',
              'uri': 'kingston',
              'similar': ''
            }
          ]
        },
        'filterable': {
          'sticker': {
            'black_friday': False,
            'show_flashsale': False,
            'uu_dai_tet': False
          },
          'is_installment': 0,
          'stock_available_id': 46,
          'company_stock_id': 46,
          'is_parent': True,
          'price': 1960000.0,
          'prices': {
            'root': {
              'chiet_khau': 0,
              'discount_id': 0,
              'discount_value': 0,
              'value': 1960000
            },
            'smem': {
              'chiet_khau': 15000,
              'discount_id': 0,
              'discount_value': 0,
              'value': 735000
            },
            'smem_student': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'smem_teacher': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'snew': {
              'chiet_khau': 8000,
              'discount_id': 0,
              'discount_value': 0,
              'value': 743000
            },
            'snew_student': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'snew_teacher': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'snull_student': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'snull_teacher': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'special': {
              'chiet_khau': 0,
              'discount_id': 4923,
              'discount_value': 1210000,
              'value': 750000
            },
            'svip': {
              'chiet_khau': 23000,
              'discount_id': 0,
              'discount_value': 0,
              'value': 728000
            },
            'svip_student': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            },
            'svip_teacher': {
              'chiet_khau': 0,
              'discount_id': 5811,
              'discount_value': 38000,
              'value': 712000
            }
          },
          'special_price': 750000,
          'promotion_information': '',
          'thumbnail': '/g/r/group_304.png',
          'promotion_pack': {
            
          },
          'flash_sale_types': None
        }
      }
    ]
  }
}
'''