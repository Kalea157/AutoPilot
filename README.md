# Münster Reinigung - Professionelle Reinigungsdienstleistungen

Eine vollständig responsive, moderne Webseite für ein professionelles Reinigungsunternehmen in Münster (PLZ 48167).

## 🚀 Features

### ✅ Vollständig implementiert:
- **Responsive Design** - Optimiert für alle Geräte (Desktop, Tablet, Mobile)
- **Moderne UI/UX** - Dunkles Theme mit professionellem Design
- **Vollständige Dienstleistungen** - Alle 8 gewünschten Reinigungsservices
- **Kontaktformular** - Mit E-Mail & WhatsApp-Integration
- **Google Maps Integration** - Interaktive Karte mit dunklem Theme
- **DSGVO-konformer Cookie-Banner** - Mit Speicherung der Nutzerentscheidung
- **Rechtliche Seiten** - Impressum, Datenschutz & AGB automatisch generiert
- **Kundenbewertungen** - Interaktiver Slider mit Touch-Support
- **FAQ-Bereich** - Akkordeon-Style mit Smooth-Animationen
- **Smooth Scrolling** - Professionelle Navigation
- **Mobile Navigation** - Hamburger-Menu für mobile Geräte
- **SEO-optimiert** - Meta-Tags, strukturierte Daten, Performance

### 🎨 Design Features:
- **Dunkles Theme** - Moderne, professionelle Farbpalette
- **Animierte Elemente** - Hover-Effekte, Transitions, Parallax
- **Font Awesome Icons** - Konsistente Iconographie
- **Google Fonts (Inter)** - Moderne, lesbare Typografie
- **CSS Grid & Flexbox** - Moderne Layout-Techniken
- **CSS Custom Properties** - Wartbare, konsistente Styles

### 📱 Responsive Breakpoints:
- **Desktop**: 1200px+
- **Tablet**: 768px - 1199px
- **Mobile**: 480px - 767px
- **Small Mobile**: < 480px

## 📁 Projektstruktur

```
muenster-reinigung/
├── index.html                 # Hauptseite
├── impressum.html            # Impressum
├── datenschutz.html          # Datenschutzerklärung
├── agb.html                  # Allgemeine Geschäftsbedingungen
├── css/
│   ├── style.css             # Haupt-Stylesheet
│   └── responsive.css        # Responsive Design
├── js/
│   ├── main.js               # Haupt-JavaScript
│   ├── slider.js             # Bewertungs-Slider
│   └── contact.js            # Kontaktformular & Maps
├── assets/                   # Bilder & Medien
│   ├── logo.png             # Firmenlogo
│   ├── favicon.ico          # Favicon
│   ├── hero-bg.jpg          # Hero-Hintergrund
│   ├── about-team.jpg       # Team-Bild
│   ├── services/            # Service-Bilder
│   │   ├── dachreinigung.jpg
│   │   ├── fassadenreinigung.jpg
│   │   ├── terrassenreinigung.jpg
│   │   ├── hofreinigung.jpg
│   │   ├── maschinenreinigung.jpg
│   │   ├── graffitientfernung.jpg
│   │   ├── zaunreinigung.jpg
│   │   └── bauendreinigung.jpg
│   └── reviews/             # Kundenbilder
│       ├── customer1.jpg
│       ├── customer2.jpg
│       ├── customer3.jpg
│       └── customer4.jpg
└── README.md                # Diese Datei
```

## 🛠️ Installation & Setup

### 1. Projekt herunterladen
```bash
git clone [repository-url]
cd muenster-reinigung
```

### 2. Lokaler Server starten
```bash
# Mit Python 3
python -m http.server 8000

# Mit Node.js (http-server)
npx http-server

# Mit PHP
php -S localhost:8000
```

### 3. Browser öffnen
```
http://localhost:8000
```

## ⚙️ Konfiguration

### Google Maps API Key
In `index.html` Zeile 25 den API-Key ersetzen:
```html
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&callback=initMap" async defer></script>
```

### Kontaktdaten anpassen
In allen HTML-Dateien die Kontaktdaten aktualisieren:
- Telefonnummer: `0123 456789`
- E-Mail: `info@muenster-reinigung.de`
- Adresse: `Musterstraße 123, 48167 Münster`

### WhatsApp-Nummer
In `js/contact.js` Zeile 280 die WhatsApp-Nummer anpassen:
```javascript
whatsappBtn.href = 'https://wa.me/49123456789?text=...';
```

## 🎯 Dienstleistungen

Die Webseite präsentiert folgende 8 Hauptdienstleistungen:

1. **Dachreinigung** - Moos, Algen, Flechten entfernen
2. **Fassadenreinigung** - Putz, Klinker, Beton, Holz, Metall
3. **Terrassen- & Gehwegreinigung** - Pflaster, Beton, Holz
4. **Hof- & Garagenreinigung** - Parkplätze, Einfahrten
5. **Maschinen- & Fahrzeugreinigung** - Bau- & Landmaschinen, LKW
6. **Graffitientfernung** - Beton, Putz, Metall
7. **Zaun- & Gartenelemente** - Holz, Stein, Metall
8. **Bauendreinigung** - Innen und außen

## 📞 Kontakt & Integration

### Kontaktformular Features:
- **E-Mail Integration** - Automatische E-Mail-Generierung
- **WhatsApp Integration** - Direkte WhatsApp-Nachrichten
- **API-Backend** - Vorbereitet für Server-Integration
- **Formular-Validierung** - Client-seitige Validierung
- **Auto-Save** - Lokale Speicherung der Eingaben
- **Service-Auswahl** - Automatische Nachrichten-Vorlagen

### WhatsApp Quick-Contact:
- **Floating Button** - Pulsierender WhatsApp-Button
- **Direkte Nachrichten** - Vordefinierte Nachrichten
- **Mobile-optimiert** - Touch-freundlich

## 🎨 Design System

### Farbpalette:
```css
--primary-color: #2563eb;      /* Blau */
--secondary-color: #10b981;    /* Grün */
--accent-color: #f59e0b;       /* Orange */
--bg-primary: #0f172a;         /* Dunkelblau */
--bg-secondary: #1e293b;       /* Mittleres Blau */
--text-primary: #f8fafc;       /* Weiß */
--text-secondary: #cbd5e1;     /* Hellgrau */
```

### Typografie:
- **Font**: Inter (Google Fonts)
- **Gewichte**: 300, 400, 500, 600, 700
- **Responsive**: Automatische Größenanpassung

### Spacing System:
```css
--spacing-xs: 0.25rem;   /* 4px */
--spacing-sm: 0.5rem;    /* 8px */
--spacing-md: 1rem;      /* 16px */
--spacing-lg: 1.5rem;    /* 24px */
--spacing-xl: 2rem;      /* 32px */
--spacing-2xl: 3rem;     /* 48px */
--spacing-3xl: 4rem;     /* 64px */
```

## 🔧 Technische Details

### Browser-Support:
- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

### Performance:
- **Lazy Loading** - Bilder werden bei Bedarf geladen
- **CSS Optimierung** - Minimierte, effiziente Styles
- **JavaScript Modular** - Aufgeteilte, wartbare Module
- **Font Loading** - Optimierte Google Fonts

### Accessibility:
- **WCAG 2.1 AA** - Barrierefreiheit konform
- **Keyboard Navigation** - Vollständige Tastatur-Navigation
- **Screen Reader** - Optimiert für Screen Reader
- **Focus Management** - Klare Fokus-Indikatoren

## 📱 Mobile Features

### Touch-Optimierung:
- **Touch Targets** - Mindestens 44px
- **Swipe Navigation** - Bewertungs-Slider
- **Mobile Menu** - Hamburger-Navigation
- **Responsive Images** - Optimierte Bildgrößen

### Mobile Performance:
- **Reduced Motion** - Unterstützung für `prefers-reduced-motion`
- **Touch Events** - Optimierte Touch-Behandlung
- **Viewport Meta** - Korrekte Mobile-Darstellung

## 🚀 Deployment

### Für Live-Server:
1. **Domain konfigurieren**
2. **SSL-Zertifikat installieren**
3. **Google Maps API Key setzen**
4. **Kontaktdaten aktualisieren**
5. **Bilder optimieren** (WebP-Format empfohlen)

### Hosting-Empfehlungen:
- **All-Inkl** (wie in Datenschutz erwähnt)
- **Netlify** (kostenlos)
- **Vercel** (kostenlos)
- **GitHub Pages** (kostenlos)

## 📈 SEO & Marketing

### SEO-Optimierung:
- **Meta Tags** - Vollständige Meta-Informationen
- **Strukturierte Daten** - Schema.org Markup
- **Sitemap** - Automatische Sitemap-Generierung
- **Robots.txt** - Suchmaschinen-Optimierung

### Analytics Integration:
- **Google Analytics** - Vorbereitet für GA4
- **Facebook Pixel** - Conversion-Tracking
- **Conversion Tracking** - Formular-Submissions

## 🔒 Datenschutz & Rechtliches

### DSGVO-Konformität:
- **Cookie-Banner** - DSGVO-konform
- **Datenschutzerklärung** - Vollständig und aktuell
- **Impressum** - Rechtlich korrekt
- **AGB** - Professionelle Geschäftsbedingungen

### Datenschutz-Features:
- **Cookie-Management** - Lokale Speicherung der Entscheidung
- **Formular-Daten** - Sichere Verarbeitung
- **Tracking-Opt-Out** - Einfache Deaktivierung

## 🛠️ Wartung & Updates

### Regelmäßige Updates:
- **Bilder aktualisieren** - Neue Projektbilder
- **Bewertungen** - Neue Kundenbewertungen
- **Preise** - Aktuelle Preislisten
- **Kontaktdaten** - Änderungen der Kontaktdaten

### Technische Wartung:
- **Dependencies** - Font Awesome, Google Fonts
- **Browser-Support** - Neue Browser-Versionen
- **Performance** - Regelmäßige Optimierung

## 📞 Support

Bei Fragen oder Problemen:
- **E-Mail**: info@muenster-reinigung.de
- **Telefon**: 0123 456789
- **Website**: www.muenster-reinigung.de

## 📄 Lizenz

© 2024 Münster Reinigung. Alle Rechte vorbehalten.

---

**Entwickelt mit ❤️ für professionelle Reinigungsdienstleistungen in Münster**
