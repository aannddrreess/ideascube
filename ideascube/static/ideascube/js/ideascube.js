/*global Minislate document window Pikaday console gettext*/
/* eslint new-cap:0, strict:0, quotes:[2, "single"] global-strict:0, no-underscore-dangle:0, curly:0, consistent-return:0, no-new:0, no-console:0, space-before-function-paren:[2, "always"] */
'use strict';

ID.http = {

    _ajax: function (settings) {
        var xhr = new window.XMLHttpRequest();
        xhr.open(settings.verb, settings.uri, true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                settings.callback.call(settings.context || xhr, xhr.status, xhr.responseText, xhr);
            }
        };
        xhr.send(settings.data);
        return xhr;
    },

    get: function (uri, options) {
        options.verb = 'GET';
        options.uri = uri;
        return ID.http._ajax(options);
    },

    queryString: function (params) {
        var queryString = [];
        for (var key in params) {
            queryString.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key]));
        }
        return queryString.join('&');
    }

};

ID.OembedDialog = Minislate.Class(Minislate.controls.Dialog, {
    show: function (node) {
        var control = this.control,
            editor = this.toolbar.editor,
            selection = Minislate.rangy.saveSelection(), input;

       editor.showDialog(function () {
            input.focus();
        });

        input = this.addTextField('URL: ', {
            escape: function () {
                editor.restoreSelection(selection);
            },
            enter: function (evt) {
                editor.restoreSelection(selection);
                control.saveOembed(node, evt.target.value);
            }
        });

        this.addButton('Save', {
            fontAwesomeID: 'check',
            click: function (evt) {
                evt.stopImmediatePropagation();
                editor.restoreSelection(selection);
                control.saveOembed(node, input.value);
            }
        });

        if (node) {
            input.value = node.getAttribute('data-url');
            this.addButton('Remove', {
                fontAwesomeID: 'times',
                click: function (evt) {
                    evt.stopImmediatePropagation();
                    editor.restoreSelection(selection);
                    control.saveOembed(node, null);
                }
            });
        }
    }
});

ID.Oembed = Minislate.Class(Minislate.controls.Button, {
    defaults: Minislate.extend({}, Minislate.controls.Button.prototype.defaults, {
        label: 'Embeded',
        title: 'Embeded content',
        fontAwesomeID: 'youtube-play'
    }),

    CONTAINER_CLASS: 'minislate-oembed-container',

    PROVIDERS: {
        '^(http(s)?://)?(www\.)?(youtube\.com|youtu\.be)': 'http://www.youtube.com/oembed',
        '^(http(s)?://)?(www\.)?dailymotion\.com': 'http://www.dailymotion.com/services/oembed',
        '^(https?://)?vimeo.com/': 'http://vimeo.com/api/oembed.json',
        '^(https?://)?(www\.)?flickr.com/': 'https://www.flickr.com/services/oembed/'
    },

    filterContainer: function (node) {
        return node.nodeName.toLowerCase() === 'div' && node.className === this.CONTAINER_CLASS;
    },

    getContainer: function () {
        var self = this;
        return this.toolbar.editor.getTopNodes(function (node) { return self.filterContainer(node);})[0];
    },

    isEmptyNode: function () {
        var node = this.toolbar.editor.getEnclosingNode();
        return node && !node.textContent;
    },

    isHighlighted: function () {
        return !!this.getContainer();
    },

    isVisible: function () {
        return !!this.getContainer() || this.isEmptyNode();
    },

    click: function () {
        (new ID.OembedDialog(this)).show(this.getContainer());
    },

    matchProvider: function (value) {
        this.PROVIDERS['^(https?://)?((www\.)?' + ID.DOMAIN + '/|localhost)'] = window.location.origin + window.location.pathname.slice(0, 3) + '/mediacenter/oembed/';
        for (var provider in this.PROVIDERS) {
            if (value.match(provider)) return this.PROVIDERS[provider];
        }
    },

    saveOembed: function (node, url) {
        var editor = this.toolbar.editor,
            range = editor.getRange();

        if (!url) {
            if (node) node.parentNode.removeChild(node);
            editor.showToolbar();
            return;
        }

        var callback = function (status, resp) {
            if (status === 200) {
                try {
                    resp = JSON.parse(resp);
                } catch (e) {
                    return;
                }
                if (node && url) {
                    node.setAttribute('data-url', url);
                    editor.setRange(node);
                } else if (url) {
                    node = document.createElement('div');
                    node.setAttribute('data-url', url);
                    node.setAttribute('class', 'minislate-oembed-container');
                    range.deleteContents();
                    range.insertNode(node);
                    editor.cleanBlock(node.parentNode);
                    editor.setRange(node);
                }
                if (resp.type === 'photo') {
                    var img = document.createElement('IMG');
                    img.setAttribute('src', resp.url);
                    node.appendChild(img);
                } else if (resp.type === 'video' || resp.type === 'rich') {
                    node.innerHTML = resp.html;
                }
                editor.showToolbar();
            }
        };
        var providerUrl = this.matchProvider(url);
        if (providerUrl) {
            var finalUrl = providerUrl + '?' + ID.http.queryString({url: url, format: 'json', maxwidth: '800'});
            var proxyUrl = '/ajax-proxy/?' + ID.http.queryString({url: finalUrl});
            ID.http.get(proxyUrl, {
                callback: callback
            });
        }
    }
});

ID.editor = Minislate.Class(Minislate.Editor, {
    init: function () {
        Minislate.Editor.prototype.init.apply(this, arguments);

        this.toolbar.addControl(Minislate.controls.Menu, 'blocks', {
            label: '¶',
            title: 'Blocks',
            controls: [
                [Minislate.controls.block.Paragraph, 'p'],
                [Minislate.controls.block.H1, 'h1'],
                [Minislate.controls.block.H2, 'h2'],
                [Minislate.controls.block.H3, 'h3'],
                [Minislate.controls.block.Preformated, 'pre']
            ]
        });
        this.toolbar.addControl(Minislate.controls.Menu, 'lists', {
            label: 'Lists',
            title: 'Lists',
            fontAwesomeID: 'list-ul',
            controls: [
                [Minislate.controls.block.UnorderedList, 'ul'],
                [Minislate.controls.block.OrderedList, 'ol']
            ]
        });
        this.toolbar.addControl(Minislate.controls.block.Blockquote, 'quote');
        this.toolbar.addControl(Minislate.controls.inline.Bold, 'bold');
        this.toolbar.addControl(Minislate.controls.inline.Italic, 'italic');
        this.toolbar.addControl(Minislate.controls.inline.Underline, 'underline');
        this.toolbar.addControl(Minislate.controls.inline.Link, 'link');
        this.toolbar.addControl(ID.Oembed, 'oembed');
    }
});

ID.initEditor = function (name) {
    var input = document.querySelector('[name="' + name + '"]');
    var label = document.querySelector('label[for="' + name + '"]');
    var element = document.querySelector('[data-editable-for="' + name + '"]');
    if (!input || !element) return console.error('Missing elements for editor ' + name);
    input.style.display = 'none';
    if (label) label.style.display = 'none';
    new ID.editor(element);
    input.form.onsubmit = function () {
        input.innerHTML = element.innerHTML;
    };
};

ID.initDatepicker = function (name) {
    new Pikaday({
        field: document.querySelector('[name="' + name + '"]'),
        format: 'YYYY-MM-DD',
        i18n: {
            previousMonth: gettext('Previous Month'),
            nextMonth: gettext('Next Month'),
            months: [gettext('January'), gettext('February'), gettext('March'), gettext('April'), gettext('May'), gettext('June'), gettext('July'), gettext('August'), gettext('September'), gettext('October'), gettext('November'), gettext('December')],
            weekdays: [gettext('Sunday'), gettext('Monday'), gettext('Tuesday'), gettext('Wednesday'), gettext('Thursday'), gettext('Friday'), gettext('Saturday')],
            weekdaysShort: [gettext('Sun'), gettext('Mon'), gettext('Tue'), gettext('Wed'), gettext('Thu'), gettext('Fri'), gettext('Sat')]
        }
    });
};

ID.focusOn = function (selector) {
    var element = document.querySelector(selector);
    if (element) element.focus();
};

ID.endswith = function (str, suffix) {
    return str.indexOf(suffix, str.length - suffix.length) !== -1;
};

ID.stopEnterKey = function (name) {
    var el = document.querySelector('[name="' + name + '"]');
    if (!el) return;
    var stop = function (e) {
        if (e.keyCode === 13) e.preventDefault();
    };
    el.addEventListener('keydown', stop, false);
};

ID.confirmClick = function (selector) {
    var el = document.querySelector(selector);
    if (!el) return;
    var ask = function (e) {
        if (!confirm(gettext('Are you sure?'))) {
            e.preventDefault();
            return false;
        }
    };
    el.addEventListener('click', ask, false);
};


ID.initWifiList = function (item_selector, popup_selector, urlroot) {
    var elements = document.querySelectorAll(item_selector);

    for (var i = 0; i < elements.length; ++i) {
        var element = elements[i];
        var known = element.getAttribute('data-known') === 'True';
        var secure = element.getAttribute('data-secure') === 'True';

        if (known || !secure) {
            var ssid = element.getAttribute('data-ssid');
            element.setAttribute('href', urlroot + ssid);
        } else {
            element.setAttribute('href', popup_selector);

            element.addEventListener('click', function (evt) {
                var ssid = this.getAttribute('data-ssid');
                var form = document.querySelector(popup_selector + ' form');
                form.setAttribute('action', urlroot + ssid);
            }.bind(element), true);
        }
    }
};


ID.viewablePassword = function () {
    var el = document.querySelector('input[type="password"]');
    if (!el) return;
    var wrapper = document.createElement('div'),
        button = document.createElement('i'),
        form = el.form;
    el.parentNode.insertBefore(wrapper, el);
    wrapper.appendChild(el);
    el.className = el.className + ' showable-password';
    button.className = 'fa fa-eye show-password';
    wrapper.appendChild(button);
    var show = function (e) {
        el.type = 'text';
        window.setTimeout(hide, 1000);
    };
    var hide = function (e) {
        el.type = 'password';
    };
    button.addEventListener('click', show, false);
    form.addEventListener('submit', hide, false);
};


ID.initComboBoxEntries = function () {
    function ComboBoxEntry(container) {
        this.entry = container.querySelector('input[type="text"]');
        this.hidden_entry = container.querySelector('input[type="hidden"]');
        this.button = container.querySelector('button');
        this.option_list = container.querySelector('ul');
        this.options = this.option_list.querySelectorAll('li');

        this.show_options = function() {
            var text = this.entry.value.toLowerCase();
            var visible = false;

            for (var i = 0; i < this.options.length; i++) {
                var option = this.options[i];

                if (option.textContent.toLowerCase().indexOf(text) === 0) {
                    option.style.display = 'block';
                    visible = true;
                } else {
                    option.style.display = 'none';
                }
            }

            if (visible) {
                this.option_list.style.display = 'block';
            } else {
                this.hide_options();
            }
        };

        this.hide_options = function() {
            this.option_list.style.display = 'none';
        };

        this.hide_options_delayed = function() {
            setTimeout(function() {
                if (document.activeElement !== this.entry) {
                    this.hide_options();
                }
            }.bind(this), 200);
        };

        this.button.onblur = this.hide_options_delayed.bind(this);
        this.button.onclick = function() {
            if (this.option_list.style.display === 'block') {
                this.hide_options();
            } else {
                this.show_options();
                this.entry.select();
            }
        }.bind(this);

        this.entry.onblur = this.hide_options_delayed.bind(this);
        this.entry.onfocus = this.show_options.bind(this);
        this.entry.oninput = function() {
            this.hidden_entry.value = this.entry.value;
            this.show_options();
        }.bind(this);

        for (var i = 0; i < this.options.length; i++) {
            var option = this.options[i];

            option.onclick = function(e) {
                this.entry.value = e.target.textContent;
                this.hidden_entry.value = e.target.getAttribute('data-value');
                this.hide_options();
            }.bind(this);
        }
    };

    var comboboxentries = document.querySelectorAll('.comboboxentry');

    for (var i = 0; i < comboboxentries.length; i++) {
        var comboboxentry = new ComboBoxEntry(comboboxentries[i]);
    }
};
