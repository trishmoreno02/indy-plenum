import sys

import pytest


def test_propagate_primary_is_Master_update_watermarks(checkpoint_service):
    # expected behaviour is that h must be set as last ordered ppSeqNo
    checkpoint_service._is_master = True
    checkpoint_service._data.low_watermark = 0
    checkpoint_service._data.last_ordered_3pc = (checkpoint_service.view_no, 500)
    assert checkpoint_service._data.low_watermark == 0
    checkpoint_service.update_watermark_from_3pc()
    assert checkpoint_service._data.low_watermark == 500


def test_propagate_primary_is_Master_watermarks_not_changed_if_last_ordered_not_changed(checkpoint_service):
    checkpoint_service._is_master = True
    checkpoint_service._data.low_watermark = 0
    assert checkpoint_service._data.low_watermark == 0
    checkpoint_service.update_watermark_from_3pc()
    assert checkpoint_service._data.low_watermark == 0


@pytest.mark.skip(reason="INDY-1336. For not watermarks are not dropped before new view")
def test_reset_watermarks_before_new_view(checkpoint_service, tconf, is_master):
    checkpoint_service._is_master = is_master
    checkpoint_service._data.low_watermark = 100
    checkpoint_service.reset_watermarks_before_new_view()
    assert checkpoint_service._data.low_watermark == 0
    assert checkpoint_service._data.high_watermark == tconf.LOG_SIZE
