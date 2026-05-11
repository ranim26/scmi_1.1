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
            ['th', ['class']]
        ]);
    }

    sanitize(html) {
        if (!html || typeof html !== 'string') {
            return '';
        }

        // Create a temporary DOM element to parse HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        return this.sanitizeNode(tempDiv).innerHTML;
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
        
        // Remove dangerous attributes
        const dangerousAttrs = new Set([
            'onclick', 'onload', 'onerror', 'onmouseover',
            'onmouseout', 'onfocus', 'onblur', 'onchange',
            'onsubmit', 'onreset', 'onselect', 'onunload',
            'javascript:', 'vbscript:', 'data:'
        ]);

        if (dangerousAttrs.has(attrName) || value.toLowerCase().includes('javascript:') || 
            value.toLowerCase().includes('vbscript:') || value.toLowerCase().includes('data:')) {
            return '';
        }

        // For href attributes, ensure they start with http, https, #, or mailto:
        if (attrName === 'href') {
            const lowerValue = value.toLowerCase().trim();
            if (lowerValue.startsWith('javascript:') || lowerValue.startsWith('vbscript:') || 
                lowerValue.startsWith('data:') || lowerValue.startsWith('file:')) {
                return '#';
            }
        }

        // Basic sanitization for other attributes
        return value.replace(/[<>"']/g, '');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HTMLSanitizer;
} else {
    window.HTMLSanitizer = HTMLSanitizer;
}
