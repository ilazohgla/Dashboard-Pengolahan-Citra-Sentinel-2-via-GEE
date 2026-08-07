<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" version="1.0.0" xmlns:gml="http://www.opengis.net/gml" xmlns:sld="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc">
  <UserLayer>
    <sld:LayerFeatureConstraints>
      <sld:FeatureTypeConstraint/>
    </sld:LayerFeatureConstraints>
    <sld:UserStyle>
      <sld:Name>LULC 7 Kelas</sld:Name>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ChannelSelection>
              <sld:GrayChannel>
                <sld:SourceChannelName>1</sld:SourceChannelName>
              </sld:GrayChannel>
            </sld:ChannelSelection>
            <sld:ColorMap type="values">
              <sld:ColorMapEntry color="#e53935" label="Built-up (Area Terbangun)" quantity="1"/>
              <sld:ColorMapEntry color="#f4b400" label="Cropland (Lahan Pertanian)" quantity="2"/>
              <sld:ColorMapEntry color="#2e7d32" label="Forest (Hutan)" quantity="3"/>
              <sld:ColorMapEntry color="#1e88e5" label="Water (Perairan)" quantity="4"/>
              <sld:ColorMapEntry color="#9e9d24" label="Bare Land (Lahan Terbuka)" quantity="5"/>
              <sld:ColorMapEntry color="#6d4c41" label="Shrub &amp; Grassland (Semak/Padang Rumput)" quantity="6"/>
              <sld:ColorMapEntry color="#26a69a" label="Wetland (Lahan Basah)" quantity="7"/>
            </sld:ColorMap>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </UserLayer>
</StyledLayerDescriptor>
