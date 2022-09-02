from prometheus_client import multiprocess

def child_exit(_, worker):
    multiprocess.mark_process_dead(worker.pid)