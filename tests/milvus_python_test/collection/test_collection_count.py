import pdb
import copy
import logging
import itertools
from time import sleep
import threading
from multiprocessing import Process
import sklearn.preprocessing

import pytest
from utils import *
from constants import *

uid = "collection_count"
tag = "collection_count_tag"

class TestCollectionCount:
    """
    params means different nb, the nb value may trigger merge, or not
    """
    @pytest.fixture(
        scope="function",
        params=[
            1,
            1000,
            2001
        ],
    )
    def insert_count(self, request):
        yield request.param

    """
    generate valid create_index params
    """
    @pytest.fixture(
        scope="function",
        params=gen_simple_index()
    )
    def get_simple_index(self, request, connect):
        if str(connect._cmd("mode")[1]) == "CPU":
            if request.param["index_type"] in index_cpu_not_support():
                pytest.skip("sq8h not support in cpu mode")
        request.param.update({"metric_type": "L2"})
        return request.param

    def test_collection_count(self, connect, collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection and add vectors in it,
            assert the value returned by count_entities method is equal to length of vectors
        expected: the count is equal to the length of vectors
        '''
        entities = gen_entities(insert_count)
        res = connect.bulk_insert(collection, entities)
        connect.flush([collection])
        res = connect.count_entities(collection)
        assert res == insert_count

    def test_collection_count_partition(self, connect, collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection, create partition and add vectors in it,
            assert the value returned by count_entities method is equal to length of vectors
        expected: the count is equal to the length of vectors
        '''
        entities = gen_entities(insert_count)
        connect.create_partition(collection, tag)
        res_ids = connect.bulk_insert(collection, entities, partition_tag=tag)
        connect.flush([collection])
        res = connect.count_entities(collection)
        assert res == insert_count

    def test_collection_count_multi_partitions_A(self, connect, collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection, create partitions and add entities in it,
            assert the value returned by count_entities method is equal to length of entities
        expected: the count is equal to the length of entities
        '''
        new_tag = "new_tag"
        entities = gen_entities(insert_count)
        connect.create_partition(collection, tag)
        connect.create_partition(collection, new_tag)
        res_ids = connect.bulk_insert(collection, entities)
        connect.flush([collection])
        res = connect.count_entities(collection)
        assert res == insert_count

    def test_collection_count_multi_partitions_B(self, connect, collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection, create partitions and add entities in one of the partitions,
            assert the value returned by count_entities method is equal to length of entities
        expected: the count is equal to the length of entities
        '''
        new_tag = "new_tag"
        entities = gen_entities(insert_count)
        connect.create_partition(collection, tag)
        connect.create_partition(collection, new_tag)
        res_ids = connect.bulk_insert(collection, entities, partition_tag=tag)
        connect.flush([collection])
        res = connect.count_entities(collection)
        assert res == insert_count

    def test_collection_count_multi_partitions_C(self, connect, collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection, create partitions and add entities in one of the partitions,
            assert the value returned by count_entities method is equal to length of entities
        expected: the count is equal to the length of vectors
        '''
        new_tag = "new_tag"
        entities = gen_entities(insert_count)
        connect.create_partition(collection, tag)
        connect.create_partition(collection, new_tag)
        res_ids = connect.bulk_insert(collection, entities)
        res_ids_2 = connect.bulk_insert(collection, entities, partition_tag=tag)
        connect.flush([collection])
        res = connect.count_entities(collection)
        assert res == insert_count * 2

    def test_collection_count_multi_partitions_D(self, connect, collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection, create partitions and add entities in one of the partitions,
            assert the value returned by count_entities method is equal to length of entities
        expected: the collection count is equal to the length of entities
        '''
        new_tag = "new_tag"
        entities = gen_entities(insert_count)
        connect.create_partition(collection, tag)
        connect.create_partition(collection, new_tag)
        res_ids = connect.bulk_insert(collection, entities, partition_tag=tag)
        res_ids2 = connect.bulk_insert(collection, entities, partition_tag=new_tag)
        connect.flush([collection])
        res = connect.count_entities(collection)
        assert res == insert_count * 2

    def _test_collection_count_after_index_created(self, connect, collection, get_simple_index, insert_count):
        '''
        target: test count_entities, after index have been created
        method: add vectors in db, and create index, then calling count_entities with correct params 
        expected: count_entities raise exception
        '''
        entities = gen_entities(insert_count)
        res = connect.bulk_insert(collection, entities)
        connect.flush([collection])
        connect.create_index(collection, default_float_vec_field_name, get_simple_index)
        res = connect.count_entities(collection)
        assert res == insert_count

    def test_count_without_connection(self, collection, dis_connect):
        '''
        target: test count_entities, without connection
        method: calling count_entities with correct params, with a disconnected instance
        expected: count_entities raise exception
        '''
        with pytest.raises(Exception) as e:
            dis_connect.count_entities(collection)

    def test_collection_count_no_vectors(self, connect, collection):
        '''
        target: test collection rows_count is correct or not, if collection is empty
        method: create collection and no vectors in it,
            assert the value returned by count_entities method is equal to 0
        expected: the count is equal to 0
        '''    
        res = connect.count_entities(collection)
        assert res == 0


class TestCollectionCountIP:
    """
    params means different nb, the nb value may trigger merge, or not
    """
    @pytest.fixture(
        scope="function",
        params=[
            1,
            1000,
            2001
        ],
    )
    def insert_count(self, request):
        yield request.param

    """
    generate valid create_index params
    """
    @pytest.fixture(
        scope="function",
        params=gen_simple_index()
    )
    def get_simple_index(self, request, connect):
        if str(connect._cmd("mode")[1]) == "CPU":
            if request.param["index_type"] in index_cpu_not_support():
                pytest.skip("sq8h not support in cpu mode")
        request.param.update({"metric_type": "IP"})
        return request.param

    def _test_collection_count_after_index_created(self, connect, collection, get_simple_index, insert_count):
        '''
        target: test count_entities, after index have been created
        method: add vectors in db, and create index, then calling count_entities with correct params 
        expected: count_entities raise exception
        '''
        entities = gen_entities(insert_count)
        res = connect.bulk_insert(collection, entities)
        connect.flush([collection])
        connect.create_index(collection, field_name, get_simple_index)
        res = connect.count_entities(collection)
        assert res == insert_count


class TestCollectionCountBinary:
    """
    params means different nb, the nb value may trigger merge, or not
    """
    @pytest.fixture(
        scope="function",
        params=[
            1,
            1000,
            2001
        ],
    )
    def insert_count(self, request):
        yield request.param

    @pytest.fixture(
        scope="function",
        params=gen_simple_index()
    )
    def get_jaccard_index(self, request, connect):
        if request.param["index_type"] in binary_support():
            request.param["metric_type"] = "JACCARD"
            return request.param
        else:
            pytest.skip("Skip index")

    @pytest.fixture(
        scope="function",
        params=gen_simple_index()
    )
    def get_hamming_index(self, request, connect):
        if request.param["index_type"] in binary_support():
            request.param["metric_type"] = "HAMMING"
            return request.param
        else:
            pytest.skip("Skip index")

    @pytest.fixture(
        scope="function",
        params=gen_simple_index()
    )
    def get_substructure_index(self, request, connect):
        if request.param["index_type"] == "FLAT":
            request.param["metric_type"] = "SUBSTRUCTURE"
            return request.param
        else:
            pytest.skip("Skip index")

    @pytest.fixture(
        scope="function",
        params=gen_simple_index()
    )
    def get_superstructure_index(self, request, connect):
        if request.param["index_type"] == "FLAT":
            request.param["metric_type"] = "SUPERSTRUCTURE"
            return request.param
        else:
            pytest.skip("Skip index")

    def test_collection_count(self, connect, binary_collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection and add entities in it,
            assert the value returned by count_entities method is equal to length of entities
        expected: the count is equal to the length of entities
        '''
        raw_vectors, entities = gen_binary_entities(insert_count)
        res = connect.bulk_insert(binary_collection, entities)
        logging.getLogger().info(len(res))
        connect.flush([binary_collection])
        res = connect.count_entities(binary_collection)
        assert res == insert_count

    def test_collection_count_partition(self, connect, binary_collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection, create partition and add entities in it,
            assert the value returned by count_entities method is equal to length of entities
        expected: the count is equal to the length of entities
        '''
        raw_vectors, entities = gen_binary_entities(insert_count)
        connect.create_partition(binary_collection, tag)
        res_ids = connect.bulk_insert(binary_collection, entities, partition_tag=tag)
        connect.flush([binary_collection])
        res = connect.count_entities(binary_collection)
        assert res == insert_count

    @pytest.mark.level(2)
    def test_collection_count_multi_partitions_A(self, connect, binary_collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection, create partitions and add entities in it,
            assert the value returned by count_entities method is equal to length of entities
        expected: the count is equal to the length of entities
        '''
        new_tag = "new_tag"
        raw_vectors, entities = gen_binary_entities(insert_count)
        connect.create_partition(binary_collection, tag)
        connect.create_partition(binary_collection, new_tag)
        res_ids = connect.bulk_insert(binary_collection, entities)
        connect.flush([binary_collection])
        res = connect.count_entities(binary_collection)
        assert res == insert_count

    @pytest.mark.level(2)
    def test_collection_count_multi_partitions_B(self, connect, binary_collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection, create partitions and add entities in one of the partitions,
            assert the value returned by count_entities method is equal to length of entities
        expected: the count is equal to the length of entities
        '''
        new_tag = "new_tag"
        raw_vectors, entities = gen_binary_entities(insert_count)
        connect.create_partition(binary_collection, tag)
        connect.create_partition(binary_collection, new_tag)
        res_ids = connect.bulk_insert(binary_collection, entities, partition_tag=tag)
        connect.flush([binary_collection])
        res = connect.count_entities(binary_collection)
        assert res == insert_count

    def test_collection_count_multi_partitions_C(self, connect, binary_collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection, create partitions and add entities in one of the partitions,
            assert the value returned by count_entities method is equal to length of entities
        expected: the count is equal to the length of entities
        '''
        new_tag = "new_tag"
        raw_vectors, entities = gen_binary_entities(insert_count)
        connect.create_partition(binary_collection, tag)
        connect.create_partition(binary_collection, new_tag)
        res_ids = connect.bulk_insert(binary_collection, entities)
        res_ids_2 = connect.bulk_insert(binary_collection, entities, partition_tag=tag)
        connect.flush([binary_collection])
        res = connect.count_entities(binary_collection)
        assert res == insert_count * 2

    @pytest.mark.level(2)
    def test_collection_count_multi_partitions_D(self, connect, binary_collection, insert_count):
        '''
        target: test collection rows_count is correct or not
        method: create collection, create partitions and add entities in one of the partitions,
            assert the value returned by count_entities method is equal to length of entities
        expected: the collection count is equal to the length of entities
        '''
        new_tag = "new_tag"
        raw_vectors, entities = gen_binary_entities(insert_count)
        connect.create_partition(binary_collection, tag)
        connect.create_partition(binary_collection, new_tag)
        res_ids = connect.bulk_insert(binary_collection, entities, partition_tag=tag)
        res_ids2 = connect.bulk_insert(binary_collection, entities, partition_tag=new_tag)
        connect.flush([binary_collection])
        res = connect.count_entities(binary_collection)
        assert res == insert_count * 2

    def _test_collection_count_after_index_created(self, connect, binary_collection, get_jaccard_index, insert_count):
        '''
        target: test count_entities, after index have been created
        method: add vectors in db, and create index, then calling count_entities with correct params 
        expected: count_entities raise exception
        '''
        raw_vectors, entities = gen_binary_entities(insert_count)
        res = connect.bulk_insert(binary_collection, entities)
        connect.flush([binary_collection])
        connect.create_index(binary_collection, field_name, get_jaccard_index)
        res = connect.count_entities(binary_collection)
        assert res == insert_count

    def _test_collection_count_after_index_created(self, connect, binary_collection, get_hamming_index, insert_count):
        '''
        target: test count_entities, after index have been created
        method: add vectors in db, and create index, then calling count_entities with correct params 
        expected: count_entities raise exception
        '''
        raw_vectors, entities = gen_binary_entities(insert_count)
        res = connect.bulk_insert(binary_collection, entities)
        connect.flush([binary_collection])
        connect.create_index(binary_collection, field_name, get_hamming_index)
        res = connect.count_entities(binary_collection)
        assert res == insert_count

    def test_collection_count_no_entities(self, connect, binary_collection):
        '''
        target: test collection rows_count is correct or not, if collection is empty
        method: create collection and no vectors in it,
            assert the value returned by count_entities method is equal to 0
        expected: the count is equal to 0
        '''    
        res = connect.count_entities(binary_collection)
        assert res == 0


class TestCollectionMultiCollections:
    """
    params means different nb, the nb value may trigger merge, or not
    """
    @pytest.fixture(
        scope="function",
        params=[
            1,
            1000,
            2001
        ],
    )
    def insert_count(self, request):
        yield request.param
        
    @pytest.fixture(
        scope="function",
        params=gen_simple_index()
    )
    def get_jaccard_index(self, request, connect):
        if request.param["index_type"] in binary_support():
            request.param["metric_type"] = "JACCARD"
            return request.param
        else:
            pytest.skip("Skip index")

    @pytest.fixture(
        scope="function",
        params=gen_simple_index()
    )
    def get_hamming_index(self, request, connect):
        if request.param["index_type"] in binary_support():
            request.param["metric_type"] = "HAMMING"
            return request.param
        else:
            pytest.skip("Skip index")

    @pytest.fixture(
        scope="function",
        params=gen_simple_index()
    )
    def get_substructure_index(self, request, connect):
        if request.param["index_type"] == "FLAT":
            request.param["metric_type"] = "SUBSTRUCTURE"
            return request.param
        else:
            pytest.skip("Skip index")

    @pytest.fixture(
        scope="function",
        params=gen_simple_index()
    )
    def get_superstructure_index(self, request, connect):
        if request.param["index_type"] == "FLAT":
            request.param["metric_type"] = "SUPERSTRUCTURE"
            return request.param
        else:
            pytest.skip("Skip index")

    def test_collection_count_multi_collections_l2(self, connect, insert_count):
        '''
        target: test collection rows_count is correct or not with multiple collections of L2
        method: create collection and add entities in it,
            assert the value returned by count_entities method is equal to length of entities
        expected: the count is equal to the length of entities
        '''
        entities = gen_entities(insert_count)
        collection_list = []
        collection_num = 20
        for i in range(collection_num):
            collection_name = gen_unique_str(uid)
            collection_list.append(collection_name)
            connect.create_collection(collection_name, default_fields)
            res = connect.bulk_insert(collection_name, entities)
        connect.flush(collection_list)
        for i in range(collection_num):
            res = connect.count_entities(collection_list[i])
            assert res == insert_count

    @pytest.mark.level(2)
    def test_collection_count_multi_collections_binary(self, connect, binary_collection, insert_count):
        '''
        target: test collection rows_count is correct or not with multiple collections of JACCARD
        method: create collection and add entities in it,
            assert the value returned by count_entities method is equal to length of entities
        expected: the count is equal to the length of entities
        '''
        raw_vectors, entities = gen_binary_entities(insert_count)
        res = connect.bulk_insert(binary_collection, entities)
        collection_list = []
        collection_num = 20
        for i in range(collection_num):
            collection_name = gen_unique_str(uid)
            collection_list.append(collection_name)
            connect.create_collection(collection_name, default_binary_fields)
            res = connect.bulk_insert(collection_name, entities)
        connect.flush(collection_list)
        for i in range(collection_num):
            res = connect.count_entities(collection_list[i])
            assert res == insert_count

    @pytest.mark.level(2)
    def test_collection_count_multi_collections_mix(self, connect):
        '''
        target: test collection rows_count is correct or not with multiple collections of JACCARD
        method: create collection and add entities in it,
            assert the value returned by count_entities method is equal to length of entities
        expected: the count is equal to the length of entities
        '''
        collection_list = []
        collection_num = 20
        for i in range(0, int(collection_num / 2)):
            collection_name = gen_unique_str(uid)
            collection_list.append(collection_name)
            connect.create_collection(collection_name, default_fields)
            res = connect.bulk_insert(collection_name, default_entities)
        for i in range(int(collection_num / 2), collection_num):
            collection_name = gen_unique_str(uid)
            collection_list.append(collection_name)
            connect.create_collection(collection_name, default_binary_fields)
            res = connect.bulk_insert(collection_name, default_binary_entities)
        connect.flush(collection_list)
        for i in range(collection_num):
            res = connect.count_entities(collection_list[i])
            assert res == default_nb
