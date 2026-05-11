// Basic HTML Sanitizer for preventing XSS attacks
class HTMLSanitizer {
    constructor() {
        this.allowedTags = new Set([
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'br', 'strong', 'em', 'i', 'b',
            'ul', 'ol', 'li', 'dl', 'dt', 'dd',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'div', 'span', 'a', 'img', 'hr',
            'small', 'blockquote', 'code', 'pre'
        ]);
        
        this.allowedAttributes = new Map([
            ['a', ['href', 'title', 'target']],
            ['img', ['src', 'alt', 'width', 'height', 'title']],
            ['td', ['colspan', 'rowspan']],
            ['th', ['colspan', 'rowspan', 'scope']],
            ['div', ['class']],
            ['span', ['class']],
            ['p', ['class']],
            ['small', ['class']],
            ['strong', ['class']],
            ['em', ['class']],
            ['i', ['class']],
            ['b', ['class']],
            ['ul', ['class']],
            ['ol', ['class']],
            ['li', ['class']],
            ['table', ['class']],
            ['thead', ['class']],
            ['tbody', ['class']],
            ['tr', ['class']],
            ['td', ['class']],
            ['th', ['class']],
            ['h1', ['class']],
            ['h2', ['class']],
            ['h3', ['class']],
            ['h4', ['class']],
            ['h5', ['class']],
            ['h6', ['class']],
            ['blockquote', ['class']],
            ['code', ['class']],
            ['pre', ['class']]
        ]);
    }

    sanitize(html) {
        if (!html || typeof html !== 'string') {
            return '';
        }

        // Use DOMParser for safer HTML parsing to prevent execution during parsing
        let doc;
        try {
            const parser = new DOMParser();
            doc = parser.parseFromString(html, 'text/html');
        } catch (e) {
            // Fallback to safer method if DOMParser fails
            const tempDiv = document.createElement('template');
            tempDiv.innerHTML = html;
            doc = tempDiv.content;
        }
        
        // Create a container element for sanitized content
        const container = document.createElement('div');
        const sanitizedNode = this.sanitizeNode(doc.body);
        
        if (sanitizedNode && sanitizedNode.nodeType === Node.ELEMENT_NODE) {
            container.appendChild(sanitizedNode);
        } else if (sanitizedNode) {
            container.appendChild(sanitizedNode);
        }
        
        return container.innerHTML;
    }

    sanitizeNode(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return node;
        }

        if (node.nodeType === Node.ELEMENT_NODE) {
            const tagName = node.tagName.toLowerCase();
            
            // Remove script tags and dangerous elements
            if (this.isDangerousTag(tagName)) {
                return document.createTextNode('');
            }

            // Check if tag is allowed
            if (!this.allowedTags.has(tagName)) {
                // Keep the content but remove the tag
                const textContent = node.textContent || '';
                return document.createTextNode(textContent);
            }

            // Create new element with allowed attributes
            const newNode = document.createElement(tagName);
            
            // Copy allowed attributes
            const allowedAttrs = this.allowedAttributes.get(tagName) || [];
            for (const attr of node.attributes) {
                if (allowedAttrs.includes(attr.name.toLowerCase())) {
                    // Sanitize attribute values
                    const sanitizedValue = this.sanitizeAttribute(attr.name, attr.value);
                    if (sanitizedValue) {
                        newNode.setAttribute(attr.name, sanitizedValue);
                    }
                }
            }

            // Recursively sanitize child nodes
            while (node.firstChild) {
                const sanitizedChild = this.sanitizeNode(node.firstChild);
                newNode.appendChild(sanitizedChild);
            }

            return newNode;
        }

        // For other node types, create empty text node
        return document.createTextNode('');
    }

    isDangerousTag(tagName) {
        const dangerousTags = new Set([
            'script', 'iframe', 'object', 'embed', 'form',
            'input', 'button', 'select', 'textarea',
            'link', 'meta', 'style', 'base'
        ]);
        return dangerousTags.has(tagName.toLowerCase());
    }

    sanitizeAttribute(name, value) {
        if (!value || typeof value !== 'string') {
            return '';
        }

        const attrName = name.toLowerCase();
        
        // Remove dangerous attributes (fixed: removed href and src from dangerousAttrs)
        const dangerousAttrs = new Set([
            'onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout', 'onfocus', 'onblur',
            'onchange', 'onsubmit', 'onreset', 'onselect', 'onunload', 'onmouseenter', 'onmouseleave',
            'onkeydown', 'onkeyup', 'onkeypress', 'onmousedown', 'onmouseup', 'onmousemove',
            'ondblclick', 'oncontextmenu', 'onwheel', 'ondrag', 'ondrop', 'onscroll',
            'javascript:', 'vbscript:', 'data:'
        ]);

        if (dangerousAttrs.has(attrName)) {
            return '';
        }

        // For href and src attributes, ensure they start with safe protocols
        if (attrName === 'href' || attrName === 'src') {
            const lowerValue = value.toLowerCase().trim();
            if (lowerValue.startsWith('javascript:') || lowerValue.startsWith('vbscript:') || 
                lowerValue.startsWith('data:') || lowerValue.startsWith('file:') ||
                lowerValue.startsWith('ftp:') || lowerValue.startsWith('mailto:') ||
                lowerValue.startsWith('vbscript:') || lowerValue.includes('javascript:') ||
                lowerValue.includes('vbscript:') || lowerValue.includes('data:')) {
                return attrName === 'href' ? '#' : '';
            }
            
            // Additional validation for URLs
            try {
                const url = new URL(value, window.location.origin);
                // Only allow http, https, and relative URLs
                if (!['http:', 'https:'].includes(url.protocol) && !value.startsWith('/') && !value.startsWith('#')) {
                    return attrName === 'href' ? '#' : '';
                }
            } catch (e) {
                // Invalid URL, return safe default
                return attrName === 'href' ? '#' : '';
            }
        }

        // Enhanced sanitization for all attributes - prevent CSS injection and script execution
        return value
            .replace(/[<>"'`]/g, '')
            .replace(/javascript\s*:/gi, '')
            .replace(/vbscript\s*:/gi, '')
            .replace(/data\s*:/gi, '')
            .replace(/expression\s*\(/gi, '')
            .replace(/@import/gi, '')
            .replace(/behavior\s*:/gi, '')
            .replace(/binding\s*:/gi, '')
            .trim();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HTMLSanitizer;
} else {
    window.HTMLSanitizer = HTMLSanitizer;
}
