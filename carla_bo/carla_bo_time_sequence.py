#!/usr/bin/env python3

import carla
import random
import logging
import time
import numpy as np

from bayes_opt import BayesianOptimization
from bayes_opt import SequentialDomainReductionTransformer

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
iteration = 0

track = [[], [], [], []] # iteration, walk_x, walk_y, min_distance 

def norm_vector(vector=carla.Vector3D):
    length = (vector.x**2 + vector.y**2 + vector.z**2)**(1/2)
    return vector/length

def plot_track():
    logging.info('plotting')
    global track
    logging.info(track)
    min_distance = track[3]

    index_min = min(range(len(min_distance)), key=min_distance.__getitem__)

    print('min_distance is: {} and was found in iteration {} at x: {}, y: {}'.format(
        min_distance[index_min], 
        track[0][index_min], 
        track[1][index_min], 
        track[2][index_min]))

    print(min(track[3]))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    # ax = Axes3D(fig)

    # ax.scatter(track[1], track[2], track[3])
    ax.plot_trisurf(
        np.array(track[1]), 
        np.array(track[2]), 
        np.array(track[3]),
        cmap=plt.cm.Spectral
        )

    ax.scatter(
        track[1][index_min], 
        track[2][index_min], 
        track[3][index_min], 
        s=128, 
        c='red', 
        alpha=1
        )
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('min_distance')
    
    plt.show()


def run_scenario(x_0, x_1, x_2, x_3, x_4, x_5, x_6, x_7, x_8, x_9, y_0, y_1, y_2, y_3, y_4, y_5, y_6, y_7, y_8, y_9):
    #walk_x, walk_y):
    x_list = [x_0, x_1, x_2, x_3, x_4, x_5, x_6, x_7, x_8, x_9]
    y_list = [y_0, y_1, y_2, y_3, y_4, y_5, y_6, y_7, y_8, y_9]
    walk_x = x_list[0]
    walk_y = y_list[0]
    logging.info('init scenario with x: {}, y: {}'.format(walk_x, walk_y))
    global iteration
    global track
    iteration += 1
    logging.info('iteration: {}'.format(iteration))
    vehicles_list = []
    walkers_list = []
    all_id = []

    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0) # seconds

    synchronous_master = False

    min_distance = 1000.0

    try:
        world = client.get_world()

        # vehicles

        traffic_manager = client.get_trafficmanager(8000)
        traffic_manager.set_global_distance_to_leading_vehicle(1)
        traffic_manager.set_random_device_seed(0)

        blueprints = world.get_blueprint_library().filter('model3')

        spawn_points = world.get_map().get_spawn_points()
        
        SpawnActor = carla.command.SpawnActor
        SetAutopilot = carla.command.SetAutopilot
        # SetVehicleLightState = carla.command.SetVehicleLightState
        FutureActor = carla.command.FutureActor

        # spawn vehicle

        blueprint = blueprints[0]
        transform = spawn_points[2]

        batch = []

        # TODO what is the driver_id used for?
        if blueprint.has_attribute('driver_id'):        
            driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
            blueprint.set_attribute('driver_id', driver_id)

        blueprint.set_attribute('role_name', 'autopilot')
        batch.append(SpawnActor(blueprint, transform)
            .then(SetAutopilot(FutureActor, True, traffic_manager.get_port())))

        for response in client.apply_batch_sync(batch, synchronous_master):
            if response.error:
                logging.error(response.error)
            else:
                vehicles_list.append(response.actor_id)


        # walker
        batch = []
        transform = carla.Transform(carla.Location(x=100.647888, y=11.172070, z=1.055295), carla.Rotation(pitch=1.602929, yaw=-157.672867, roll=0.000046))
        blueprintsWalkers = world.get_blueprint_library().filter('walker.pedestrian.*')

        walker_bp = random.choice(blueprintsWalkers)

        batch.append(SpawnActor(walker_bp, transform))

        results = client.apply_batch_sync(batch, True)

        walkers_list.append({"id": results[0].actor_id})

        walker_control = carla.WalkerControl()

        walker = world.get_actor(walkers_list[0]['id'])
        walker_direction = carla.Vector3D(x = walk_x, y = walk_y)

        walker.apply_control(
                    carla.WalkerControl(
                        direction = walker_direction, 
                        speed=1
                        ))


        # spectator

        spectator = world.get_spectator()
        spectator.set_transform(transform)

        cumulative_reward = 0.0

        
        for i in range(len(x_list)):
            walker_direction = carla.Vector3D(x = x_list[i], y = x_list[i])
            walker.apply_control(
                    carla.WalkerControl(
                        direction = walker_direction, 
                        speed=1
                        ))
            vehicle = world.get_actor(vehicles_list[0])
            vehicle_location = vehicle.get_location()
            walker_location = walker.get_location()
            distance = walker_location.distance(vehicle_location)
            logging.debug('distance: {}'.format(distance))
            min_distance = min(min_distance, distance)
            logging.debug('walking_direction: {}'.format(walker_control.direction))

            time.sleep(1)



        # time.sleep(20)
    finally:
        
        logging.debug('destroying %d vehicles' % len(vehicles_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])

        logging.debug('destroying %d walkers' % len(walkers_list))
        client.apply_batch([carla.command.DestroyActor(x['id']) for x in walkers_list])

        time.sleep(0.5)
        logging.info('min_distance to vehicle: {}'.format(min_distance))
        logging.info('finished scenario \n')
        track[0].append(iteration)
        track[1].append(walk_x)
        track[2].append(walk_y)
        track[3].append(min_distance)
        return -min_distance

def main():
    start_time = time.time()
    iteration = 0

    # run_scenario(-1.3344522955990954, -0.6953082740892751)
    #run_scenario(1.0, 0.0)
    #run_scenario(0.0, 1.0)
    run_scenario(x_0= -0.7750768090284623, x_1= 1.1781157181630055, x_2= -2.0, x_3= 0.22624889884959426, x_4= -1.8071693062168928, x_5= -0.9759442272469341, x_6= -1.4016624734203218, x_7= -0.21744511187233925, x_8= -0.5174869410031995, x_9= 0.11077977549303636, y_0= -1.215880406042104, y_1= 0.13930334215392173, y_2= -1.8060465883366803, y_3= -0.2637782061745287, y_4= -1.014170606327852, y_5= 1.739060008211137, y_6= -1.0689642649426279, y_7= 1.5799232677858592, y_8= -0.5896139558573852, y_9= -1.5161041780876645)

    pbounds = {
        'x_0': (-2.0, 2.0), 
        'x_1': (-2.0, 2.0), 
        'x_2': (-2.0, 2.0), 
        'x_3': (-2.0, 2.0), 
        'x_4': (-2.0, 2.0), 
        'x_5': (-2.0, 2.0), 
        'x_6': (-2.0, 2.0), 
        'x_7': (-2.0, 2.0), 
        'x_8': (-2.0, 2.0), 
        'x_9': (-2.0, 2.0), 
        'y_0': (-2.0, 2.0), 
        'y_1': (-2.0, 2.0), 
        'y_2': (-2.0, 2.0), 
        'y_3': (-2.0, 2.0), 
        'y_4': (-2.0, 2.0), 
        'y_5': (-2.0, 2.0), 
        'y_6': (-2.0, 2.0), 
        'y_7': (-2.0, 2.0), 
        'y_8': (-2.0, 2.0), 
        'y_9': (-2.0, 2.0), 
        }
    bounds_transformer = SequentialDomainReductionTransformer()

    optimizer = BayesianOptimization(
        f=run_scenario,
        pbounds=pbounds,
        verbose=2, 
        random_state=1,
        bounds_transformer=bounds_transformer
    )

    optimizer.maximize(
        init_points=5,
        n_iter=20,
    )

    logging.info(optimizer.max)
    logging.info('duration: {}'.format(time.time()-start_time))
    plot_track()
    logging.info('bounds: {}'.format(bounds_transformer))


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        logging.info('done')