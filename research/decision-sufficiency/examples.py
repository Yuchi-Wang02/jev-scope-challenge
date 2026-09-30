"""Authored toy contracts and expected outcomes, not independent annotations."""
import copy


def base():
    return {'version': 1,
            'payment_methods': {'card_A': 'ordinary', 'card_B': 'ordinary',
                                'card_C': 'ordinary', 'gift_G': 'gift_card'},
            'original_method_universe': ['card_A', 'card_B', 'card_C'],
            'request': {'selector': {'kind': 'product', 'value': 'mug'}, 'destination_id': 'card_A'},
            'records': [record('order_1', ['card_A'])],
            'retrieval': {'query': {'kind': 'product', 'value': 'mug'},
                          'additional_matches': 'none', 'omitted_original_methods': []}}


def record(order_id, methods, product='mug'):
    return {'order_id': order_id, 'product': product, 'original_methods': methods}


def cases():
    result = []
    def add(case_id, title, state, predicate, unique, explanation):
        result.append({'case_id': case_id, 'title': title, 'contract': copy.deepcopy(state),
                       'expected': {'predicate_only': predicate, 'unique_target_required': unique},
                       'explanation': explanation})
    V, I, U = 'VALID_DESTINATION', 'INVALID_DESTINATION', 'NOT_ESTABLISHED'
    s = base()
    add('s01', 'One known order, original method', s, V, V, 'Both interfaces have enough information.')
    s['request']['destination_id'] = 'card_B'
    add('s02', 'One known order, another ordinary method', s, I, I, 'An ordinary method in the profile is not enough.')
    s = base(); s['records'].append(record('order_2', ['card_A']))
    add('s03', 'Two orders, same original method', s, V, U, 'The predicate is invariant; identity is not established.')
    s['request']['destination_id'] = 'card_C'
    add('s04', 'Two orders, destination invalid for both', s, I, U, 'Certain falsity also need not identify the order.')
    s = base(); s['records'].append(record('order_2', ['card_B']))
    add('s05', 'Two orders, opposite answers', s, U, U, 'One consistent target accepts; another rejects.')
    s['request']['destination_id'] = 'gift_G'
    add('s06', 'Two orders, existing gift-card exception', s, V, U, 'The stated exception holds for either target, but does not authorize execution.')
    s = base(); s['retrieval'].update(additional_matches='possible', omitted_original_methods=['card_A', 'card_B'])
    add('s07', 'One visible match, unknown completeness', s, U, U, 'The missing candidate can reverse the predicate.')
    s['request']['destination_id'] = 'gift_G'
    add('s08', 'Unknown completeness, gift-card exception', s, V, U, 'A visible match guarantees existence; the exception covers every possible target.')
    s = base(); s['retrieval'].update(additional_matches='at_least_one', omitted_original_methods=['card_A'])
    add('s09', 'Omitted candidates share the same original method', s, V, U, 'The supplied domain is a synthetic contract assertion, not an inferred fact.')
    s['request']['destination_id'] = 'card_C'
    add('s10', 'Omitted candidates cannot use this destination', s, I, U, 'No consistent target has card_C as its original method.')
    s = base(); s['records'][0]['original_methods'] = ['card_A', 'card_B']
    add('s11', 'Unique identity, unresolved original payment', s, U, U, 'Knowing which order does not resolve its payment predicate.')
    s['request']['destination_id'] = 'gift_G'
    add('s12', 'Unique identity, gift card bypasses missing original', s, V, V, 'The exception suffices for this component despite an unresolved original method.')
    s = base(); s['records'] = []; s['request']['destination_id'] = 'gift_G'
    add('s13', 'No matching order in a complete query', s, U, U, 'No target is not a vacuously valid refund destination.')
    s['retrieval'].update(additional_matches='possible', omitted_original_methods=['card_A', 'card_B'])
    add('s14', 'No visible match, existence unknown, gift card', s, U, U, 'A world with no matching target prevents a determined component answer.')
    s['retrieval']['additional_matches'] = 'at_least_one'
    add('s15', 'Existence guaranteed, unseen identity, gift card', s, V, U, 'Existence and the exception suffice for the predicate, not an order ID.')
    s = base(); s['request']['selector'] = {'kind': 'order_id', 'value': 'order_1'}
    s['retrieval']['query'] = copy.deepcopy(s['request']['selector'])
    s['retrieval'].update(additional_matches='possible', omitted_original_methods=['card_B'])
    add('s16', 'Visible exact ID with a loose completeness bound', s, V, V, 'The unique-ID constraint excludes an additional matching order; possible is an upper bound.')
    s = base(); s['request']['destination_id'] = None
    add('s17', 'Destination not identified', s, U, U, 'A missing destination is not a known invalid destination.')
    s = base(); s['request']['destination_id'] = 'gift_NOT_IN_PROFILE'
    add('s18', 'Named but nonexistent gift card', s, I, I, 'Names do not create the existing-gift-card exception; the method universe is complete.')
    s = base(); s['records'].append(record('unrelated', ['card_B'], 'lamp'))
    add('s19', 'An unrelated record changes neither interface', s, V, V, 'The contract and selection remain scoped to mug.')
    s = base(); s['records'] = []; s['request']['selector'] = {'kind': 'order_id', 'value': 'order_9'}
    s['retrieval'].update(query=copy.deepcopy(s['request']['selector']), additional_matches='at_least_one', omitted_original_methods=['card_A'])
    add('s20', 'Exact unseen ID, existence and payment guaranteed', s, V, V, 'The synthetic contract guarantees this exact ID exists with one original method.')
    return result


def invalid_cases():
    out = []
    s = base(); s['records'].append(copy.deepcopy(s['records'][0]))
    out.append(('e01_duplicate_id', s))
    s = base(); s['records'][0]['original_methods'] = []
    out.append(('e02_empty_domain', s))
    s = base(); s['retrieval']['query']['value'] = 'lamp'
    out.append(('e03_wrong_query_scope', s))
    s = base(); s['request']['selector'] = {'kind': 'order_id', 'value': 'order_1'}
    s['retrieval'].update(query=copy.deepcopy(s['request']['selector']), additional_matches='at_least_one', omitted_original_methods=['card_A'])
    out.append(('e04_impossible_unique_id', s))
    s = base(); s['records'][0]['original_methods'] = ['unlisted_card']
    out.append(('e05_outside_finite_universe', s))
    return [{'case_id': name, 'contract': value, 'expected_status': 'INVALID_CONTRACT'} for name, value in out]
