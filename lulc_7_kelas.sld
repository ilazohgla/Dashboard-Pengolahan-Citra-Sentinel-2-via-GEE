<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" version="1.0.0" xmlns:ogc="http://www.opengis.net/ogc">
  <NamedLayer>
    <Name>LULC 7 Kelas</Name>
    <UserStyle>
      <Name>LULC 7 Kelas</Name>
      <Title>LULC 7 Kelas</Title>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ChannelSelection>
              <GrayChannel>
                <SourceChannelName>1</SourceChannelName>
              </GrayChannel>
            </ChannelSelection>
            <ColorMap type="values">
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
