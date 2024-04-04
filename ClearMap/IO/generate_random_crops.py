# Import necessary libraries
import os
import numpy as np
from tifffile import TiffFile,imread, imwrite
from sklearn.model_selection import train_test_split

# Define the crop_select function
def crop_select(image, window_size=(200, 250, 250)):
    # Create a new image shape that the original image will fit
    original_shape = image.shape
    newshape = [window_size[f]*(image.shape[f]//window_size[f]) for f in range(3)]

    # Crop the original image to fit
    image = image[:newshape[0], :newshape[1], :newshape[2]]

    # Calculate how many windows fit along each dimension
    num_windows = [original_shape[i] // window_size[i] for i in range(3)]

    # Calculate the shape of the reshaped image
    new_shape = (num_windows[0], window_size[0], num_windows[1], window_size[1], num_windows[2], window_size[2])

    # Reshape the image to create non-overlapping windows
    reshaped_image = np.reshape(image, new_shape)

    # Calculate std intensity for each window.
    std_intensities = np.std(reshaped_image, axis=(1, 3, 5))

    # Flatten and sort the windows based on the std intensities
    flat_sorted_index = np.argsort(std_intensities.flatten())[::-1]
    sorted_index = [np.unravel_index(f, reshaped_image.shape[:3]) for f in flat_sorted_index]
    sorted_index = [(f[0]*window_size[0], f[1]*window_size[1], f[2]*window_size[2]) for f in sorted_index]

    return sorted_index

# Modify generate crops of image that contain objects
def generate_crops(imgfolder, n_crops,zoffsets = 100,  crop_size=(50, 250, 250), crop_per_stack = 3):
    # get the list of image files
    # the function is expecting a list of tif images contained in the imgfolder
    filenames = [os.path.join(imgfolder,f) for f in np.sort(os.listdir(imgfolder)) if '.tif' in f]

    # start a loop to crop images
    crops = []
    while len(crops) < n_crops:
        for i in range(crop_per_stack):
            if not len(crops) < n_crops:
                break
            print("Generating crop {} of {}".format(len(crops)+1, n_crops))
            z = np.random.randint(zoffsets, len(filenames) - crop_size[0] - zoffsets)
            #y = np.random.randint(offsets[1], imshape[0] - crop_size[1] - offsets[1])
            #x = np.random.randint(offsets[2], imshape[1] - crop_size[2] - offsets[2])

            image_z_stack = imread(filenames[z:z+crop_size[0]])
            #image_z_stack = [TiffFile(filenames[z_idx]).asarray(out='memmap')[y:y+crop_size[1], x:x+crop_size[2]] for z_idx in range(z, z+crop_size[0])]
            #image_z_stack = np.stack(image_z_stack, axis=0)

            # Use crop_select to get the best area
            sorted_indices = crop_select(image_z_stack, crop_size)

            # Select the first index (best area)
            selected_index = sorted_indices[i+3] # dont pick up the first 3, since it may contain strong noise

            crop = image_z_stack[selected_index[0]:selected_index[0]+crop_size[0],
                                selected_index[1]:selected_index[1]+crop_size[1],
                                selected_index[2]:selected_index[2]+crop_size[2]]
            if crop.shape == crop_size:
                crops.append(crop)
            else:
                print("crop is not in shape")
    return crops

# Rest of the code remains the same...

def main(input_folder, output_folder, fkey, n_crops, test_proportion = 0.2, zoffsets = 100, crop_size=(50, 250, 250),crop_per_stack = 3):
    crops = generate_crops(input_folder, n_crops,zoffsets = 100,  crop_size=crop_size, crop_per_stack = crop_per_stack)

    train_imgs, test_imgs = train_test_split(crops, test_size=test_proportion)

    train_folder = os.path.join(output_folder, 'train')
    test_folder = os.path.join(output_folder, 'test')

    if not os.path.exists(train_folder):
        os.makedirs(train_folder)

    if not os.path.exists(test_folder):
        os.makedirs(test_folder)

    for i, img in enumerate(train_imgs):
        imwrite(os.path.join(train_folder,  fkey + '_train_{}.tif'.format(i+1)), img)

    for i, img in enumerate(test_imgs):
        imwrite(os.path.join(test_folder, fkey + '_test_{}.tif'.format(i+1)), img)

if __name__ == "__main__":
    input_folder = r"\\128.95.12.251\Analysis2\Ken\LSMS\c-Fos_Sample_Data\20240205_14_18_17_IM3_c_Fos_Destripe_DONE\Ex_639_Ch2_stitched"
    output_folder = r"C:\Users\stuberadmin\Desktop\ilastik_segmentation\test"
    crop_size=(50, 250, 250)
    n_crops = 5
    test_proportion = 0.2
    zoffsets = 100
    fkey = '20240205_14_18_17_IM3_c_Fos_Destripe_DONE_2'
    print("Generating random crops...")
    main(   input_folder, 
            output_folder, 
            fkey, 
            n_crops, 
            test_proportion = test_proportion, 
            zoffsets = zoffsets, 
            crop_size=crop_size,
            crop_per_stack = 3)
