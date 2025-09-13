<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="html" encoding="UTF-8" indent="yes"/>

    <!-- Template raíz: construye la página HTML y delega el render de cada <book> -->
    <xsl:template match="/">
        <html lang="es">
            <head>
                <meta charset="UTF-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1"/>
                <title>Catálogo de libros</title>
                <link rel="stylesheet" href="catalogo_libros.css"/>
            </head>
            <body>
                <div class="catalog">
                    <h1 class="catalog-title">Catálogo de Libros</h1>
                    <div class="books-grid">
                        <!-- Aplica la plantilla de cada libro -->
                        <xsl:apply-templates select="catalog/book"/>
                    </div>
                </div>
            </body>
        </html>
    </xsl:template>

    <!-- Template para cada libro -->
    <xsl:template match="book">
        <div class="book-card">
            <!-- Insignia de formato con clase condicional -->
            <span class="format-badge">
                <xsl:attribute name="class">
                    <xsl:text>format-badge </xsl:text>
                    <xsl:choose>
                        <xsl:when test="format = 'Físico'">format-fisico</xsl:when>
                        <xsl:otherwise>format-digital</xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
                <xsl:value-of select="format"/>
            </span>

            <div class="book-title">
                <xsl:value-of select="title"/>
            </div>
            <div class="book-author">
                por <xsl:value-of select="author"/>
            </div>

            <div class="book-details">
                <div class="book-detail">
                    <span class="book-detail-label">Género:</span>
                    <span class="book-detail-value genre"><xsl:value-of select="genre"/></span>
                </div>
                <div class="book-detail">
                    <span class="book-detail-label">Año:</span>
                    <span class="book-detail-value year"><xsl:value-of select="year"/></span>
                </div>
            </div>

            <div class="book-price-stock">
                <span class="price">$<xsl:value-of select="price"/></span>
                <span>
                    <xsl:attribute name="class">
                        <xsl:text>stock </xsl:text>
                        <xsl:choose>
                            <xsl:when test="number(stock) &lt;= 10">low</xsl:when>
                            <xsl:when test="number(stock) &lt;= 30">medium</xsl:when>
                            <xsl:otherwise>high</xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                    <span class="stock-indicator">
                        <xsl:attribute name="class">
                            <xsl:text>stock-indicator </xsl:text>
                            <xsl:choose>
                                <xsl:when test="number(stock) &lt;= 10">low</xsl:when>
                                <xsl:when test="number(stock) &lt;= 30">medium</xsl:when>
                                <xsl:otherwise>high</xsl:otherwise>
                            </xsl:choose>
                        </xsl:attribute>
                    </span>
                    <xsl:text/>Stock: <xsl:value-of select="stock"/>
                </span>
            </div>

            <span class="isbn">ISBN: <xsl:value-of select="@isbn"/></span>
        </div>
    </xsl:template>

</xsl:stylesheet>





