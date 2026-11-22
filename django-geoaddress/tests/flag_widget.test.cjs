const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(
    path.join(__dirname, '../src/django_geoaddress/static/js/geoaddress_autocomplete.js'),
    'utf8',
);

function setup(fetch) {
    let timer;
    const document = {addEventListener() {}, body: null};
    class MutationObserver {
        observe() {}
    }
    const context = {
        document, MutationObserver, fetch, AbortController, URLSearchParams,
        console,
        setTimeout(callback) { timer = callback; return 1; },
        clearTimeout() { timer = null; },
    };
    vm.runInNewContext(source + '\nglobalThis.updateFlag = updateFlag;', context);
    const classes = new Set(['geoaddress-autocomplete-hidden']);
    const flag = {
        classList: {
            contains: (name) => classes.has(name),
            add: (name) => classes.add(name),
            remove: (name) => classes.delete(name),
        },
        removeAttribute() { delete this.src; },
    };
    return {
        updateFlag: context.updateFlag,
        field: {flag, flagUrl: '/flag-url/'},
        flag,
        classes,
        runTimer() { if (timer) timer(); },
    };
}

test('flag follows edited country code and clears invalid values', async () => {
    const requests = [];
    const state = setup(async (url) => {
        requests.push(url);
        return {ok: true, json: async () => ({flag_url: '/flags/FR.png'})};
    });

    state.updateFlag(state.field, ' fr ');
    state.runTimer();
    await new Promise(setImmediate);
    assert.deepEqual(requests, ['/flag-url/?country_code=fr']);
    assert.equal(state.flag.src, '/flags/FR.png');
    assert.equal(state.classes.has('geoaddress-autocomplete-hidden'), false);

    state.updateFlag(state.field, '');
    assert.equal(state.flag.src, undefined);
    assert.equal(state.classes.has('geoaddress-autocomplete-hidden'), true);
});

test('a late response cannot replace a newer country flag', async () => {
    const replies = [];
    const state = setup(() => new Promise((resolve) => replies.push(resolve)));

    state.updateFlag(state.field, 'FR');
    state.runTimer();
    state.updateFlag(state.field, 'CA');
    state.runTimer();
    replies[1]({ok: true, json: async () => ({flag_url: '/flags/CA.png'})});
    await new Promise(setImmediate);
    replies[0]({ok: true, json: async () => ({flag_url: '/flags/FR.png'})});
    await new Promise(setImmediate);

    assert.equal(state.flag.src, '/flags/CA.png');
});

test('selecting an autocomplete result refreshes the flag', async () => {
    let result;
    let timer;
    const makeElement = () => ({
        dataset: {},
        classList: {contains: () => false, add() {}, remove() {}},
        addEventListener(_name, callback) { this.click = callback; },
        appendChild(child) { result = child; },
        querySelector() { return null; },
    });
    const document = {
        addEventListener() {},
        createElement: makeElement,
        body: null,
    };
    class MutationObserver {
        observe() {}
    }
    const context = {
        document, MutationObserver, AbortController, URLSearchParams, console,
        window: {location: {pathname: '/admin/'}},
        setTimeout(callback) { timer = callback; return 1; },
        clearTimeout() {},
        fetch: async (url) => ({
            ok: true,
            json: async () => url.startsWith('/search')
                ? {addresses: [{country_code: 'fr', city: 'Paris'}]}
                : {flag_url: '/flags/FR.png'},
        }),
    };
    vm.runInNewContext(
        source + '\nglobalThis.fields = fields; globalThis.search = fetch_addresses;',
        context,
    );
    const flag = makeElement();
    flag.removeAttribute = () => { delete flag.src; };
    const country = {name: 'address_country_code', value: ''};
    context.fields.address = {
        list: makeElement(), results: makeElement(), loading: makeElement(),
        wrapper: makeElement(), dataInputs: [country],
        textarea: {}, searchInput: {}, flag, flagUrl: '/flag-url/',
        url: '/search',
    };

    context.search('address', 'Paris');
    await new Promise(setImmediate);
    result.click();
    timer();
    await new Promise(setImmediate);

    assert.equal(country.value, 'fr');
    assert.equal(flag.src, '/flags/FR.png');
});

test('changelist preview links to the correct object', () => {
    const document = {
        addEventListener() {},
        querySelector() { throw new Error('Should use the explicit object id'); },
        body: null,
    };
    class MutationObserver {
        observe() {}
    }
    const context = {document, MutationObserver, URLSearchParams};
    vm.runInNewContext(
        source + '\nglobalThis.buildInspectUrl = buildInspectUrl;',
        context,
    );
    const wrapper = {
        dataset: {
            inspectUrl: '/admin/inspect/',
            contentType: '3',
            fieldName: 'address',
            objectId: '42',
        },
    };

    assert.equal(
        context.buildInspectUrl(wrapper, 'address-preview-42'),
        '/admin/inspect/?content_type=3&object_id=42&field=address',
    );
});
