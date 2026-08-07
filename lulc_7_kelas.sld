<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld"
                       xmlns:ogc="http://www.opengis.net/ogc"
                       xmlns:xlink="http://www.w3.org/1999/xlink"
                       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                       version="1.0.0"
                       xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>lulc_7_kelas</Name>
    <UserStyle>
      <Title>LULC 7 Kelas</Title>
      <Abstract>Klasifikasi tutupan lahan 7 kelas (nilai piksel 1-7). Warna sinkron dengan LULC_PALETTE pada Dashboard Pengolahan Citra Sentinel-2 via GEE.</Abstract>
      <FeatureTypeStyle>
        <Name>lulc_classes_raster</Name>
        <Rule>
          <Name>lulc_color_map</Name>
          <Title>Kelas LULC 1-7</Title>
          <RasterSymbolizer>
            <Opacity>1.0</Opacity>
            <ColorMap type="intervals">
              <ColorMapEntry color="#e53935" quantity="1" label="Built-up (Area Terbangun)"/>
              <ColorMapEntry color="#f4b400" quantity="2" label="Cropland (Lahan Pertanian)"/>
              <ColorMapEntry color="#2e7d32" quantity="3" label="Forest (Hutan)"/>
              <ColorMapEntry color="#1e88e5" quantity="4" label="Water (Perairan)"/>
              <ColorMapEntry color="#9e9d24" quantity="5" label="Bare Land (Lahan Terbuka)"/>
              <ColorMapEntry color="#6d4c41" quantity="6" label="Shrub &amp; Grassland (Semak/Padang Rumput)"/>
              <ColorMapEntry color="#26a69a" quantity="7" label="Wetland (Lahan Basah)"/>
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
