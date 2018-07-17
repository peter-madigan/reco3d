from reco3d.processes.basic_processes import Process

class LArPixHitReaderProcess(Process):
    opt_resources = {}
    req_resources = {
        'in_resource': ['LArPixSerialDataResource','LArPixDataResource'],
        'out_resource': ['LArPixDataResource']
        }

    def config(self):
        super().config()

    def start(self):
        super().start()

    def run(self):
        super().run()
        # grab hits from in_resource read_queue and put them in the out_resource's queue

    def continue_run(self):
        super().continue_run()

    def finish(self):
        super().finish()

    def cleanup(self):
        super().cleanup()

class LArPixCalibrationProcess(Process):
    opt_resources = {}
    req_resources = {
        'data_resource': ['LArPixSerialDataResource','LArPixDataResource'],
        'calib_resource': ['LArPixCalibrationDataResource']
        }

    def config(self):
        super().config()

    def start(self):
        super().start()

    def run(self):
        super().run()
        # grab hit objects from data_resouce queue, apply a calibration, and put back into
        # data_resource queue

    def continue_run(self):
        super().continue_run()

    def finish(self):
        super().finish()

    def cleanup(self):
        super().cleanup()

class LArPixDataWriterProcess(Process):
    opt_resouces = {}
    req_resources = {
        'in_resource': ['LArPixSerialDataResource','LArPixDataResource'],
        'out_resource': ['LArPixDataResource']
        }

    def config(self):
        super().config()

    def start(self):
        super().start()

    def run(self):
        super().run()
        # copy objects in the in_resource queue and add them to the out_resource write_queue

    def continue_run(self):
        super().continue_run()

    def finish(self):
        super().finish()

    def cleanup(self):
        super().cleanup()
