<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34.4" minScale="1e+08" maxScale="0" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0">
  <pipe>
    <rasterrenderer alphaBand="-1" band="1" classificationMax="7" classificationMin="1" nodataColor="" opacity="1" type="paletted">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry value="1" color="#e53935" alpha="255" label="Built-up (Area Terbangun)"/>
        <paletteEntry value="2" color="#f4b400" alpha="255" label="Cropland (Lahan Pertanian)"/>
        <paletteEntry value="3" color="#2e7d32" alpha="255" label="Forest (Hutan)"/>
        <paletteEntry value="4" color="#1e88e5" alpha="255" label="Water (Perairan)"/>
        <paletteEntry value="5" color="#9e9d24" alpha="255" label="Bare Land (Lahan Terbuka)"/>
        <paletteEntry value="6" color="#6d4c41" alpha="255" label="Shrub &amp; Grassland (Semak/Padang Rumput)"/>
        <paletteEntry value="7" color="#26a69a" alpha="255" label="Wetland (Lahan Basah)"/>
      </colorPalette>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
