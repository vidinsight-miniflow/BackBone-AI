# Proje Hakkında
Bu proje MiniFlow'u geliştiriken atnı yapıları tekrar ve tekrar yazdıım süreçte kafamda oluşmaya başladı. Ben amele işi olarak sınıflandırdığım yapıları yazmak istemiyorum ama curser veya 
windsurf gibi yapılarda tam oalrka istediimi üretemiyor, girdi alam şekilleri prompt olunca ve baist düşünme özellikler eksik olunca hata çok oluyor. Bunun yanıda proje süresüde ve çapıda
uzayıp büyünce hem contezt window bakımında hem de ilişkileri takip etme açısında oldukça sorunlu bir araca dönüşüyorlar. 

Bu sebeple bunu hibrit bir şekilde yapacak, yaparkende bizim oluşturdumuz araçları kullanacak, her dilde veya bir dile ait her frameworkte değil sadece bizim çizdiğimiz sınırlarda kapsamı az
ama çıktı kalitesi yüksek olan bir destek mekanızması yapma fikrim oluştur. Bunun en basit örneği veri tabanı yapısıdır. Ben kendi adıma yapıyı tasarlamda sorun çekmem ama tabloları tek tek 
oluşturmak ve test etmek, ilişiki yapılarını ayarlamak ve dahası. Bu MiniFlow gibi 20+ tablonun olduu projelerde canımı okuyor :D

Bu sebeple tüm backendi %60 oranında kendi başına yapacak bir ai sistemi kurmak istesemde adım adım giceğiz bu sefer. Proje tasralama ve takip etmeyide ister istemez öğrendim bu süreçte. 
İlk olarka veri tabanı modellerini kusursuz doğrulukta üretecek bir destek mekanizması ile başlayacapız, detayları aşağıda bulabilirsin ama kısaca anlatmam gerekirse kullanıcı bir arayüz 
aracılığı ile veri tabanındaki tablolarının yapısını, ilişikisini, stünların parametreleri ve dahasını konfigüre edip bu sistem bir JSON olarak teslim edecek. Sisitemde bu JSON'u kullanrak
veri tabanı tablolarını oluşturacak. Bunu yaparken de sqlalchemy-engine-kit kütüphanesini temel alacak çünkü burada zarten tüm session, pool, basic tablo yapıları gibi yapıalr zaten kurulu.
Baştan yazılmısna gerek yok. Neyse çooook uzun oldu direkt projeyi analtmaya başlayayım.

## Proje Detayları
### Girdi (JSON)

```
{
  "project_name": "SimplifiedBackend",
  "db_type": "postgresql",
  "schema": [
    {
      "table_name": "users",
      "class_name": "User",
      "options": {
        "use_timestamps": true,  // TimestampMixin (created_at, updated_at) eklenecek
        "use_soft_delete": false // SoftDeleteMixin (is_deleted) eklenecek mi?
      },
      "columns": [
        {"name": "id", "type": "Integer", "primary_key": true},
        {"name": "username", "type": "String", "length": 50, "unique": true, "nullable": false},
        {"name": "status", "type": "Enum", "values": ["active", "inactive"], "default": "active"}
      ],
      "relationships": [
        {"target_table": "posts", "target_class": "Post", "type": "one_to_many", "back_populates": "author"}
      ]
    },
    {
      "table_name": "posts",
      "class_name": "Post",
      "options": {
        "use_timestamps": true,
        "use_soft_delete": true 
      },
      "columns": [
        {"name": "id", "type": "Integer", "primary_key": true},
        {"name": "title", "type": "String", "length": 200, "nullable": false},
        {"name": "author_id", "type": "ForeignKey", "target": "users.id"}
      ],
      "relationships": [
        {"target_table": "users", "target_class": "User", "type": "many_to_one", "back_populates": "posts"}
      ]
    }
  ]
}
```

Şuan bu JSON kod yazmaktan pek farklı durmasada bu bir arayüden gelecke istem bu sebeple uzun olmaıs sıkıntı değil. arayüz üzerinde bir kaç tıklama ile halledilecek. Burada önemli nokta bu yapının
sqlalchemy-engine-kit ile uyumlu çalışması. İlgili kütüphanede model oluşturma için BASE ve modelleri geliştirmek için mixinler bulunuyor. Bu mixinler eğer eklenirse otomatik sof delete stünları 
veya zaman damagaları stümnları ekleyebiliyor. JSONDA her modelin başında bulunan options, sqlalchemy-engine-kit için olan seçenkeleri tuacak. Kütüphanenin dökümanlaırna daha detaylı bakarsan daha
rahat anlarsın mutlaka.

### Projenin Çalışma Akışı
Çalışma akışı, kullanıcının sadeleştirilmiş JSON şemasını sisteme girmesiyle başlar. İlk olarak Mimar Ajan devreye girer. Bu ajanın temel görevi, gelen verinin yapısal olarak tutarlı ve 
mantıksal olarak doğru olduğunu doğrulamaktır.Mimar, tüm ForeignKey referanslarının gerçekten var olan bir tabloya işaret edip etmediğini kontrol eder (İlişkisel Bütünlük Kontrolü). Bu aşamada 
bir hata tespit edilirse, süreç durdurulur ve kullanıcıya net bir geri bildirim gönderilir. Başarılı doğrulamanın ardından, Mimar kod üretim sırasını belirleyen Dahili Yapılandırma Planını oluşturur.

**Örnek Plan**
```
A. Tablo 1: User (Kullanıcı)
Hedef Dosya: app/models/user.py
Kalıtım Sırası (Inheritance): Base, TimestampMixin
Gerekçe: JSON'da use_timestamps: true olarak işaretlenmiş.
Sütun Özeti: id (PK, Integer), username (String, Unique, Not Null).
İlişki (Relationship) Talimatı: posts = relationship("Post", back_populates="author")
Kontrol: İlişki hedefi (Post sınıfı) onaylandı.

B. Tablo 2: Post (Gönderi)
Hedef Dosya: app/models/post.py
Kalıtım Sırası (Inheritance): Base, TimestampMixin, SoftDeleteMixin
Gerekçe: JSON'da her iki Mixin de true olarak işaretlenmiş.
Sütun Özeti: id (PK, Integer), title (String, Not Null).
Foreign Key Talimatı: author_id = Column(Integer, ForeignKey("users.id"))
Kontrol: Hedef tablo users (User) mevcut.
İlişki (Relationship) Talimatı: author = relationship("User", back_populates="posts")
Kontrol: İlişki hedefi (User sınıfı) onaylandı.
```

<img width="6688" height="5650" alt="Untitled-2025-02-03-2010" src="https://github.com/user-attachments/assets/c16511cd-59f5-443c-b859-dc27c8ce1d72" />


Proje kapsamıında JSON yapıları ve plan yapısını gelişmelere ve ihtiyaçlara göre güncelelyebilirsin. Test yazma kısmı öncelikli değil sadece olsa güzel olur.
